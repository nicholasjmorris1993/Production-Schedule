import pandas as pd
import sys
sys.path.append("/home/nick/Production-Schedule/src")
from production import schedule


data = pd.read_csv("/home/nick/Production-Schedule/test/forecast.csv")

plan = schedule(data)

print(plan.demand_satisfaction)
