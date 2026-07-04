import pandas as pd
import numpy as np
from sklearn.feature_selection import mutual_info_regression
import matplotlib.pyplot as plt

df = pd.read_excel("Aedes2yrs_with_coordinates.xlsx")
# The user's dataset has eCount for mosquitos
# We need to know the shape.
print(df.head())
print(df.columns)
