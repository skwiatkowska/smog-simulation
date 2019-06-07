try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

from tkinter import messagebox

import DataHandler
import Kriging
import matplotlib
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import mplcursors
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

backgroundImage = plt.imread('krakow_targeo.png')
newCmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
X, Y, pointNames = DataHandler.readPointsParameters()
hours = DataHandler.getOneDayWeather()
dates = DataHandler.getWeekWeather()

buttonColour = "green3"
backgroundColour = "gray30"


class App(tk.Frame):
    def __init__(self, master = None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        self.running = False
        self.animation = None
        self.option = None
        self.numberOfMeasurements = None

        self.enteredWindSpeedValue = 0
        self.enteredWindDirectionValue = ""
        self.enteredTemperatureValue = 0
        self.enteredTrafficValue = 1
        self.enteredRainfallValue = 0

        buttons = tk.Frame(self)
        buttons.configure(background = backgroundColour)
        buttons.pack(expand = True)
        self.label = tk.Label(buttons, text = "SMOG SIMULATION IN KRAKOW")
        self.label.grid(row = 0, column = 0, columnspan = 4, padx = 230, pady = 10)
        self.label.config(bg = backgroundColour, fg = "white", font = ("Bahnschrift", 18))

        self.label2 = tk.Label(buttons, text = "SELECT THE LENGTH OF THE SIMULATION:")
        self.label2.grid(row = 1, column = 0)
        self.label2.config(bg = backgroundColour, fg = "white", font = ("Bahnschrift", 10))
        self.dailySimButton = tk.Button(buttons, bg = buttonColour, text = 'Daily propagation',
                                        command = lambda: self.showAskingAboutParametersWindow(0))
        self.dailySimButton.grid(row = 1, column = 1, pady = (0, 5))
        self.weeklySimButton = tk.Button(buttons, bg = buttonColour, text = 'Weekly propagation',
                                         command = lambda: self.showAskingAboutParametersWindow(1))
        self.weeklySimButton.grid(row = 1, column = 2, pady = (0, 5))
        self.pauseButton = tk.Button(buttons, bg = buttonColour, text = 'Pause', command = self.onClick)
        self.configure(background = buttonColour)

        self.fig = Figure(figsize = [8, 5])
        self.canvas = FigureCanvasTkAgg(self.fig, master = self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        self.lineBelow = tk.Label(self)
        self.lineBelow.configure(background = backgroundColour)
        self.lineBelow.pack(fill = tk.X)

    def showAskingAboutParametersWindow(self, period):

        if messagebox.askquestion("Manual parameters", "Do you want to set the parameters manually?") == 'yes':
            self.setParametersManuallyWindow(period)
        else:
            self.selectTheMeasurementPeriod(period)

    def setParametersManuallyWindow(self, period):
        self.windSpeedVar = tk.IntVar
        windDirVar = tk.StringVar
        tempVar = tk.IntVar
        trafficVar = tk.IntVar
        rainfallVar = tk.IntVar

        padyval = 5

        t = tk.Toplevel(self)
        t.wm_title("Config parameters")
        infoLabel = tk.Label(t,
                             text = "\tEnter a new value for each parameter. \n\tIf you do not want to change a particular parameter, do not enter anything in the field.\t")
        infoLabel.config(bg = backgroundColour, fg = "white", font = ("Bahnschrift", 10))
        infoLabel.pack(side = "top", fill = "both", expand = True)

        windSpeedLabel = tk.Label(t, text = "Increase/decrease the wind speed in m/s by: [e.g 3]")
        windSpeedLabel.pack()
        newWindSpeed = tk.Entry(t, textvariable = self.windSpeedVar)
        newWindSpeed.pack(pady = padyval)

        windDirectionLabel = tk.Label(t, text = "Set the wind direction to: [e.g NE]")
        windDirectionLabel.pack()
        newWindDirection = tk.Entry(t, textvariable = windDirVar)
        newWindDirection.pack(pady = padyval)

        temperatureLabel = tk.Label(t, text = "Increase/decrease the temperature in degrees Celsius by: [e.g 1]")
        temperatureLabel.pack()
        newTemperature = tk.Entry(t, textvariable = tempVar)
        newTemperature.pack(pady = padyval)

        trafficLabel = tk.Label(t, text = "Multiply a traffic level by [e.g 2]")
        trafficLabel.pack()
        newTraffic = tk.Entry(t, textvariable = trafficVar)
        newTraffic.pack(pady = padyval)

        rainfallLabel = tk.Label(t, text = "Increase/decrease the rainfall in mm by: [eg 2]")
        rainfallLabel.pack()
        newRainfall = tk.Entry(t, textvariable = rainfallVar)
        newRainfall.pack(pady = padyval)

        confirmButton = tk.Button(t, bg = buttonColour, text = 'Propagation',
                                  command = lambda: self.confirmButtonClicked(period, t, newWindSpeed, newWindDirection,
                                                                              newTemperature, newTraffic, newRainfall))
        confirmButton.pack(pady = padyval * 2)

    def confirmButtonClicked(self, period, t, newWindSpeed, newWindDirection, newTemperature, newTraffic, newRainfall):
        t.withdraw()
        self.selectTheMeasurementPeriod(period)

        self.enteredWindSpeedValue = newWindSpeed.get()
        # print(self.enteredWindSpeedValue)
        self.enteredWindDirectionValue = newWindDirection.get()
        self.enteredTemperatureValue = newTemperature.get()
        self.enteredTrafficValue = newTraffic.get()
        self.enteredRainfallValue = newRainfall.get()

    def selectTheMeasurementPeriod(self, period):
        # 0: one day, 1: one week
        self.option = period
        self.numberOfMeasurements = 8
        self.onClick()

    def onClick(self):
        if self.animation is None:
            self.dailySimButton["state"] = "disable"
            self.weeklySimButton["state"] = "disable"
            self.pauseButton.grid(row = 1, column = 3, pady = (0, 5))
            self.lineBelow.config(text = "Hover the mouse over a selected point to display its name", fg = "white",
                                  font = ("Bahnschrift", 9))
            return self.start()

        if self.running:
            self.animation.event_source.stop()
            self.pauseButton.config(text = 'Un-Pause')
        else:
            self.animation.event_source.start()
            self.pauseButton.config(text = 'Pause')
        self.running = not self.running

    def start(self):
        self.animation = animation.FuncAnimation(self.fig, self.animate, frames = self.numberOfMeasurements,
                                                 interval = 500, repeat = False)
        self.running = True
        self.pauseButton.config(text = 'Pause')
        self.animation._start()

    def createTitle(self, option, i, T, F, W, WD):
        if option == 0:
            date = dates[0]
            hour = hours[i]
        else:
            hour = '12:00'
            date = dates[i]
        title = "Date: " + date + ", Hour: " + hour + ",\nTemperature: " + str(
            round(T)) + ", Falls: " \
                + str(round(F)) + "mm, Wind: " + str(round(W)) + "m/s " + WD
        # print(T,F,W,WD+"\n")
        return title

    def animate(self, i):
        Z, T, F, W, WD = DataHandler.propagation(i, self.option, self.enteredWindSpeedValue,
                                                 self.enteredWindDirectionValue, self.enteredTemperatureValue,
                                                 self.enteredTrafficValue, self.enteredRainfallValue)
        xMesh, yMesh, zPrediction, Zi = Kriging.execute(X, Y, Z, i)
        self.fig.clf()
        subplot = self.fig.add_subplot(111)

        subplot.set_title(self.createTitle(self.option, i, T, F, W, WD))
        subplContourf = subplot.imshow(backgroundImage, extent = [0, 90, 0, 60])
        subplContourf = subplot.contourf(xMesh, yMesh, np.transpose(zPrediction), 50, cmap = newCmap, alpha = 0.6,
                                         vmin = -80,
                                         vmax = 190)
        subplContourf = subplot.scatter(X, Y, c = Zi, cmap = newCmap, vmin = 0, vmax = 80)
        colorbar = self.fig.colorbar(subplContourf, fraction = 0.03)
        colorbar.set_label('Smog level')
        cursor = mplcursors.cursor(subplContourf, hover = True)
        cursor.connect(
            "add", lambda sel: sel.annotation.set_text(pointNames[sel.target.index]))

        if i == self.numberOfMeasurements - 1:
            self.animation = None
            self.pauseButton.config(text = "Show again")
            self.dailySimButton["state"] = "normal"
            self.weeklySimButton["state"] = "normal"


def main():
    root = tk.Tk()
    root.title("Smog simulation")

    DataHandler.getSmogLevel()

    app = App(root)
    app.pack()

    def onClosing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            exit()

    root.protocol("WM_DELETE_WINDOW", onClosing)
    root.mainloop()


if __name__ == '__main__':
    main()
