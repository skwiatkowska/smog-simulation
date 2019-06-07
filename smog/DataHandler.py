import numpy as np
import pandas as pd
import requests

filename = 'punkty.xlsx'  # file with points parameters and traffic levels
weatherbitApiKey = '7d53d355b60e4980b96e9064c2498670'  # key to get weather data
airlyApiKey = '8ECT35aHdiw4Jf5A7uJcfCqNWLqJM4Ld'  # key to get smog data

dates = np.zeros(8, dtype = '<U10')  # dates for week simulation
hours = np.zeros(8, dtype = '<U5')  # hours for 24h simulation

# ids of each points of measurements
sensorID = [7514, 212, 6883, 7846, 6554, 17, 189, 1096, 8077, 58, 7394, 820, 2277, 8076, 140, 622, 1026, 196, 7661,
            195, 7956, 210, 176, 2743]

trafficLevel = np.zeros((8, 2), dtype = np.float64)
temperature = np.zeros((8, 2), dtype = np.float64)
windSpeed = np.zeros((8, 2), dtype = np.float64)
fall = np.zeros((8, 2), dtype = np.float64)
windDirection = np.zeros((8, 2), dtype = np.object)


def readPointsParameters():
    global X, Y, dataFrame, pointNames
    X = np.zeros([24], dtype = np.float64)
    Y = np.zeros([24], dtype = np.float64)
    pointNames = np.zeros([24], dtype = np.object)

    dataFrame = pd.read_excel(filename)

    for i in range(0, 24):
        X[i] = dataFrame.iat[i, 5]
        Y[i] = dataFrame.iat[i, 6]
        pointNames[i] = dataFrame.iat[i, 0]
    return X, Y, pointNames


def getSmogLevel():
    global Z, day
    Z = np.zeros((24, 8), dtype = np.float64)

    for i in range(0, 24):
        response = requests.get(
            "https://airapi.airly.eu/v2/measurements/installation?installationId=" + str(sensorID[i]),
            params = {'apikey': airlyApiKey})
        data = response.json()
        Z[i, 0] = data['current']['indexes'][0]['value']  # AIRLY CAQI
    # day = data['current']['tillDateTime'][0:10]
    checkSmogLevel()  # some points may be not available at the moment of simulation,
    #  so we have to check if the value of AIRLYCAQI is not none, if so, we change it to the value of other point


def checkSmogLevel():
    for i in range(0, 24):
        if np.isnan(Z[i, 0]):
            for j in range(0, 24):
                if not np.isnan(Z[j, 0]):
                    Z[i, 0] = Z[j, 0]
                    return


def getOneDayWeather():
    global temperature, windSpeed, fall, windDirection, trafficLevel

    response1 = requests.get(
        "https://api.weatherbit.io/v2.0/forecast/hourly?city=Krakow,PL&key=" + weatherbitApiKey + '&hours=24')
    weather = response1.json()
    for i in range(0, 8):
        if i == 0:
            x = 2
        else:
            x = i * 3 + 2

        hours[i] = weather['data'][x]['timestamp_utc'][11:16]
        temperature[i][0] = weather['data'][x]['temp']  # C
        windSpeed[i][0] = weather['data'][x]['wind_spd']  # m/s
        fall[i][0] = weather['data'][x]['precip']  # mm
        windDirection[i][0] = weather['data'][x]['wind_cdir']  # 16 directions
        if hours[i][0] == 0:
            h = int(hours[i][1])
        else:
            h = int(hours[i][0:2])
        trafficLevel[i][0] = dataFrame.iat[i, 11 + h]
    return hours


def getWeekWeather():
    global temperature, windSpeed, fall, windDirection

    response1_ = requests.get("https://api.weatherbit.io/v2.0/forecast/daily?city=Krakow,PL&key=" + weatherbitApiKey)
    weather_ = response1_.json()
    for i in range(0, 8):
        dates[i] = weather_['data'][i]['valid_date']
        temperature[i][1] = weather_['data'][i]['temp']  # C
        windSpeed[i][1] = weather_['data'][i]['wind_spd']  # m/s
        fall[i][1] = weather_['data'][i]['precip']  # mm
        windDirection[i][1] = weather_['data'][i]['wind_cdir']  # 16 directions
        trafficLevel[i][1] = dataFrame.iat[i, 11 + 12]
    return dates


def propagation(x, option, enteredWindSpeed, enteredWindDirection, enteredTemperature, enteredTraffic, enteredRainfall):
    if enteredTemperature == '':
        enteredTemperature = 0
    if enteredTraffic == '':
        enteredTraffic = 1
    if enteredRainfall == '':
        enteredRainfall = 0
    if enteredWindSpeed == '':
        enteredWindSpeed = 0
    addedFallFlag = False
    addedTrafficFlag = False
    addedTempFlag = False
    addedWindSpeedFlag = False

    if x != 0:
        if enteredWindDirection != "":
            windDirection[x][option] = enteredWindDirection
        if not addedWindSpeedFlag:
            windSpeed[x][option] = windSpeed[x][option] + int(enteredWindSpeed)
            addedWindSpeedFlag = True
        for i in range(0, 24):
            # good wind >3m/s decreases smog to minimum level
            if windSpeed[x][option] >= 3:
                Z[i, x] = Z[i, x - 1] * 0.6
            else:
                # low wind relocates smog according to its direction
                if windDirection[x][option] in ['E', 'NE', 'SE', 'ENE', 'ESE']:
                    Z[0, x] = Z[0, x - 1] * (1 - windSpeed[x][option] / 10) + Z[8, x - 1] * (windSpeed[x][option] / 20)
                    Z[1, x] = Z[1, x - 1] * (1 - windSpeed[x][option] / 10) + Z[2, x - 1] * (windSpeed[x][option] / 10)
                    Z[2, x] = Z[2, x - 1] * (1 - windSpeed[x][option] / 10) + Z[3, x - 1] * (windSpeed[x][option] / 10)
                    Z[3, x] = Z[3, x - 1] * (1 - windSpeed[x][option] / 10) + Z[5, x - 1] * (windSpeed[x][option] / 10)
                    Z[4, x] = Z[4, x - 1] * (1 - windSpeed[x][option] / 10) + Z[15, x - 1] * (windSpeed[x][option] / 20)
                    Z[5, x] = Z[5, x - 1] * (1 - windSpeed[x][option] / 10) + Z[9, x - 1] * (windSpeed[x][option] / 10)
                    Z[6, x] = Z[6, x - 1] * (1 - windSpeed[x][option] / 10) + Z[8, x - 1] * (windSpeed[x][option] / 10)
                    Z[7, x] = Z[7, x - 1] * (1 - windSpeed[x][option] / 10) + Z[8, x - 1] * (windSpeed[x][option] / 10)
                    Z[8, x] = Z[8, x - 1] * (1 - windSpeed[x][option] / 10) + Z[21, x - 1] * (windSpeed[x][option] / 30)
                    Z[9, x] = Z[9, x - 1] * (1 - windSpeed[x][option] / 10) + Z[12, x - 1] * (windSpeed[x][option] / 10)
                    Z[10, x] = Z[10, x - 1] * (1 - windSpeed[x][option] / 10) + Z[13, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[11, x] = Z[11, x - 1] * (1 - windSpeed[x][option] / 10) + Z[20, x - 1] * (
                            windSpeed[x][option] / 20)
                    Z[12, x] = Z[12, x - 1] * (1 - windSpeed[x][option] / 10) + Z[14, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[13, x] = Z[13, x - 1] * (1 - windSpeed[x][option] / 10) + Z[20, x - 1] * (
                            windSpeed[x][option] / 20)
                    Z[14, x] = Z[14, x - 1] * (1 - windSpeed[x][option] / 10) + Z[21, x - 1] * (
                            windSpeed[x][option] / 20)
                    Z[15, x] = Z[15, x - 1] * (1 - windSpeed[x][option] / 10) + Z[23, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[16, x] = Z[16, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[17, x] = Z[17, x - 1] * (1 - windSpeed[x][option] / 10) + Z[18, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[18, x] = Z[18, x - 1] * (1 - windSpeed[x][option] / 10) + Z[19, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[19, x] = Z[19, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[20, x] = Z[20, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[21, x] = Z[21, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[22, x] = Z[22, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[23, x] = Z[23, x - 1] * (1 - windSpeed[x][option] / 10) + Z[22, x - 1] * (
                            windSpeed[x][option] / 10)

                elif windDirection[x][option] in ['W', 'NW', 'SW', 'WNW', 'WSW']:
                    Z[0, x] = Z[0, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[1, x] = Z[1, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[2, x] = Z[2, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[3, x] = Z[3, x - 1] * (1 - windSpeed[x][option] / 10) + Z[2, x - 1] * (windSpeed[x][option] / 10)
                    Z[4, x] = Z[4, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[5, x] = Z[5, x - 1] * (1 - windSpeed[x][option] / 10) + Z[3, x - 1] * (windSpeed[x][option] / 10)
                    Z[6, x] = Z[6, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[7, x] = Z[7, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[8, x] = Z[8, x - 1] * (1 - windSpeed[x][option] / 10) + Z[6, x - 1] * (windSpeed[x][option] / 10)
                    Z[9, x] = Z[9, x - 1] * (1 - windSpeed[x][option] / 10) + Z[5, x - 1] * (windSpeed[x][option] / 10)
                    Z[10, x] = Z[10, x - 1] * (1 - windSpeed[x][option] / 10) + Z[5, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[11, x] = Z[11, x - 1] * (1 - windSpeed[x][option] / 10) + Z[5, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[12, x] = Z[12, x - 1] * (1 - windSpeed[x][option] / 10) + Z[9, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[13, x] = Z[13, x - 1] * (1 - windSpeed[x][option] / 10) + Z[10, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[14, x] = Z[14, x - 1] * (1 - windSpeed[x][option] / 10) + Z[12, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[15, x] = Z[15, x - 1] * (1 - windSpeed[x][option] / 10) + Z[4, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[16, x] = Z[16, x - 1] * (1 - windSpeed[x][option] / 10) + Z[0, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[17, x] = Z[17, x - 1] * (1 - windSpeed[x][option] / 10) + Z[7, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[18, x] = Z[18, x - 1] * (1 - windSpeed[x][option] / 10) + Z[17, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[19, x] = Z[19, x - 1] * (1 - windSpeed[x][option] / 10) + Z[18, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[20, x] = Z[20, x - 1] * (1 - windSpeed[x][option] / 10) + Z[13, x - 1] * (
                            windSpeed[x][option] / 20)
                    Z[21, x] = Z[21, x - 1] * (1 - windSpeed[x][option] / 10) + Z[14, x - 1] * (
                            windSpeed[x][option] / 20)
                    Z[22, x] = Z[22, x - 1] * (1 - windSpeed[x][option] / 10) + Z[23, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[23, x] = Z[23, x - 1] * (1 - windSpeed[x][option] / 10) + Z[15, x - 1] * (
                            windSpeed[x][option] / 10) - 10

                elif windDirection[x][option] in ['S', 'SSW', 'SSE']:
                    Z[0, x] = Z[0, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[1, x] = Z[1, x - 1] * (1 - windSpeed[x][option] / 10) + Z[0, x - 1] * (windSpeed[x][option] / 10)
                    Z[2, x] = Z[2, x - 1] * (1 - windSpeed[x][option] / 10) + Z[0, x - 1] * (windSpeed[x][option] / 10)
                    Z[3, x] = Z[3, x - 1] * (1 - windSpeed[x][option] / 10) + Z[4, x - 1] * (windSpeed[x][option] / 10)
                    Z[4, x] = Z[4, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[5, x] = Z[5, x - 1] * (1 - windSpeed[x][option] / 10) + Z[4, x - 1] * (windSpeed[x][option] / 10)
                    Z[6, x] = Z[6, x - 1] * (1 - windSpeed[x][option] / 10) + Z[5, x - 1] * (windSpeed[x][option] / 10)
                    Z[7, x] = Z[7, x - 1] * (1 - windSpeed[x][option] / 10) + Z[6, x - 1] * (windSpeed[x][option] / 10)
                    Z[8, x] = Z[8, x - 1] * (1 - windSpeed[x][option] / 10) + Z[16, x - 1] * (windSpeed[x][option] / 20)
                    Z[9, x] = Z[9, x - 1] * (1 - windSpeed[x][option] / 10) + Z[10, x - 1] * (windSpeed[x][option] / 10)
                    Z[10, x] = Z[10, x - 1] * (1 - windSpeed[x][option] / 10) + Z[11, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[11, x] = Z[11, x - 1] * (1 - windSpeed[x][option] / 10) + Z[15, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[12, x] = Z[12, x - 1] * (1 - windSpeed[x][option] / 10) + Z[13, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[13, x] = Z[13, x - 1] * (1 - windSpeed[x][option] / 10) + Z[15, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[14, x] = Z[14, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[15, x] = Z[15, x - 1] * (1 - windSpeed[x][option] / 10) + Z[16, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[16, x] = Z[16, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[17, x] = Z[17, x - 1] * (1 - windSpeed[x][option] / 10) + Z[14, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[18, x] = Z[18, x - 1] * (1 - windSpeed[x][option] / 10) + Z[23, x - 1] * (
                            windSpeed[x][option] / 20)
                    Z[19, x] = Z[19, x - 1] * (1 - windSpeed[x][option] / 10) + Z[20, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[20, x] = Z[20, x - 1] * (1 - windSpeed[x][option] / 10) + Z[22, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[21, x] = Z[21, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[22, x] = Z[22, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[23, x] = Z[23, x - 1] * (1 - windSpeed[x][option] / 10)

                elif windDirection[x][option] in ['N', 'NNW', 'NNE']:
                    Z[0, x] = Z[0, x - 1] * (1 - windSpeed[x][option] / 10) + Z[1, x - 1] * (windSpeed[x][option] / 10)
                    Z[1, x] = Z[1, x - 1] * (1 - windSpeed[x][option] / 10) + Z[2, x - 1] * (windSpeed[x][option] / 10)
                    Z[2, x] = Z[2, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[3, x] = Z[3, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[4, x] = Z[4, x - 1] * (1 - windSpeed[x][option] / 10) + Z[3, x - 1] * (windSpeed[x][option] / 10)
                    Z[5, x] = Z[5, x - 1] * (1 - windSpeed[x][option] / 10) + Z[6, x - 1] * (windSpeed[x][option] / 10)
                    Z[6, x] = Z[6, x - 1] * (1 - windSpeed[x][option] / 10) + Z[7, x - 1] * (windSpeed[x][option] / 10)
                    Z[7, x] = Z[7, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[8, x] = Z[8, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[9, x] = Z[9, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[10, x] = Z[10, x - 1] * (1 - windSpeed[x][option] / 10) + Z[9, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[11, x] = Z[11, x - 1] * (1 - windSpeed[x][option] / 10) + Z[10, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[12, x] = Z[12, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[13, x] = Z[13, x - 1] * (1 - windSpeed[x][option] / 10) + Z[12, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[14, x] = Z[14, x - 1] * (1 - windSpeed[x][option] / 10) + Z[17, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[15, x] = Z[15, x - 1] * (1 - windSpeed[x][option] / 10) + Z[11, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[16, x] = Z[16, x - 1] * (1 - windSpeed[x][option] / 10) + Z[10, x - 1] * (
                            windSpeed[x][option] / 20)
                    Z[17, x] = Z[17, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[18, x] = Z[18, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[19, x] = Z[19, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[20, x] = Z[20, x - 1] * (1 - windSpeed[x][option] / 10) + Z[19, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[21, x] = Z[21, x - 1] * (1 - windSpeed[x][option] / 10)
                    Z[22, x] = Z[22, x - 1] * (1 - windSpeed[x][option] / 10) + Z[20, x - 1] * (
                            windSpeed[x][option] / 10)
                    Z[23, x] = Z[23, x - 1] * (1 - windSpeed[x][option] / 10) + Z[18, x - 1] * (
                            windSpeed[x][option] / 20)
                else:
                    Z[i, x] = Z[i, x - 1] * 1

            # average temperature >-1 and <20 doesn't have a noticeable impact on smog
            # low temperature <-1 increases smog
            if not addedTempFlag:
                temperature[x][option] = temperature[x][option] + int(enteredTemperature)
                addedTempFlag = True
            if temperature[x][option] < -1:
                Z[i, x] = Z[i, x] * 1.2
            # high temperature doesn't aid low smog
            elif temperature[x][option] > 20:
                Z[i, x] = Z[i, x] * 1.2

            # fair fall significantly decreases smog
            if not addedFallFlag:
                fall[x][option] = fall[x][option] + int(enteredRainfall)
                addedFallFlag = True
            if fall[x][option] >= 1.5:
                Z[i, x] = Z[i, x] * 0.8

            # high traffic has an impact on smog
            if not addedTrafficFlag:
                trafficLevel[x][option] = trafficLevel[x][option] * int(enteredTraffic)
                addedTrafficFlag = True
            if option == 0:
                Z[i, x] += trafficLevel[x][option]
            Z[i, x] = round(Z[i, x])

    return Z, temperature[x][option], fall[x][option], windSpeed[x][option], windDirection[x][option]
