import math
import numpy as np
from numpy.linalg import inv

covariance = lambda x: 1 - (abs(x) / 10)
distance = lambda x1, y1, x2, y2: math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def execute(X, Y, Z, x):
    Zi = np.zeros([24], dtype = np.float64)
    for i in range(0, 24):
        Zi[i] = Z[i, x]

    distances = np.tile(None, (len(X), len(Y)))
    for i in range(len(X)):
        for j in range(len(Y)):
            distances[i, j] = distance(X[i], Y[i], X[j], Y[j])

    # Covariance of given data
    covariances = np.tile(None, (len(X), len(Y)))
    for row in range(len(distances[0])):
        for col in range(len(distances[1])):
            covariances[row, col] = covariance(distances[row, col])

            # Inverse Matrix
    covariancesInv = inv(np.matrix(covariances, dtype = 'float'))

    # coordinates of target points
    stride = 2  # take a target estimation point at every 2nd pixel
    xMesh = []
    for i in range(0, 92, stride):
        xMesh.append(i)

    yMesh = []
    for i in range(0, 62, stride):
        yMesh.append(i)

    # distance to target
    canvasDistance = np.tile(None, (len(xMesh), len(yMesh)))

    for j in range(len(xMesh)):
        for k in range(len(yMesh)):
            tmp = []
            for i in range(len(X)):
                tmp.append(distance(X[i], Y[i], xMesh[j], yMesh[k]))  # each target point's distance to given data
            canvasDistance[j][k] = tmp

    # Convariance of Target
    targetCovariance = np.tile(None, (len(xMesh), len(yMesh)))
    for i in range(len(xMesh)):
        for j in range(len(yMesh)):
            tmp = []
            for k in range(len(canvasDistance[i][j])):
                tmp.append(covariance(canvasDistance[i][j][k]))
            targetCovariance[i][j] = tmp

    # Weights
    covariancesInv = np.asarray(covariancesInv)
    weights = np.tile(None, (len(xMesh), len(yMesh)))
    for i in range(len(xMesh)):
        for j in range(len(yMesh)):
            weights[i, j] = np.dot(covariancesInv, targetCovariance[i][j])
    average = sum(Zi) / len(Zi)

    # Weight at zero (lambda0)
    weightSum = np.tile(None, (len(xMesh), len(yMesh)))
    for i in range(len(xMesh)):
        for j in range(len(yMesh)):
            weightSum[i, j] = sum(weights[i, j])

    lambda0 = np.tile(None, (len(xMesh), len(yMesh)))
    for i in range(len(xMesh)):
        for j in range(len(yMesh)):
            lambda0[i, j] = average * (1 - weightSum[i, j])

    # Z prediction
    weightSumInside = np.tile(None, (len(xMesh), len(yMesh)))

    for i in range(len(xMesh)):
        for j in range(len(yMesh)):
            inside = []
            for k in range(len(X)):
                inside.append(weights[i][j][k] * Zi[k])
            weightSumInside[i, j] = sum(inside)

    zPrediction = np.tile(None, (len(xMesh), len(yMesh)))
    for i in range(len(xMesh)):
        for j in range(len(yMesh)):
            zPrediction[i, j] = lambda0[i, j] + weightSumInside[i, j]

    zPrediction = zPrediction.astype(float)

    return xMesh, yMesh, zPrediction, Zi
