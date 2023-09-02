import re
import numpy as np
import pandas as pd
import plotly.express as px
from plotly.offline import plot


PERIODS = 5  # how many periods of demand should the inventory be limited to

def schedule(df):
    plan = Schedule()
    plan.production_runs(df)
    plan.plots()

    return plan

class Schedule:
    def production_runs(self, df):
        # get the products
        self.products = pd.unique(df["Product"])

        # get the initial inventory for each product
        init_inv = df.loc[df["Item"] == "Inventory"].reset_index(drop=True).copy()
        initial_inventory = dict()
        for i in range(init_inv.shape[0]):
            initial_inventory[init_inv["Product"][i]] = init_inv["Value"][i]
        
        # get the production rate for each product
        prod_rate = df.loc[df["Item"] == "Production Rate"].reset_index(drop=True).copy()
        production_rate = dict()
        for i in range(prod_rate.shape[0]):
            production_rate[prod_rate["Product"][i]] = prod_rate["Value"][i]
        
        # get the forecasted demand
        forecasted = df.loc[(df["Item"] != "Inventory") & (df["Item"] != "Production Rate")].reset_index(drop=True).copy()
        forecast = dict()
        for p in self.products:
            forecast[p] = forecasted.loc[forecasted["Product"] == p].reset_index(drop=True).copy()

        # initialize the schedule
        self.schedule = pd.DataFrame({"Period": [0], "Production": ["None"]})
        for p in self.products:
            self.schedule[f"{p}: Demand"] = 0
            self.schedule[f"{p}: Inventory"] = initial_inventory[p]
            self.schedule[f"{p}: Demand Satisfaction"] = 1

        # schedule production runs according to: run out rate = inventory / demand
        for i in range(forecast[self.products[0]].shape[0]):

            # compute the run out rate for each product
            run_out = list()
            for p in self.products:
                look_ahead = i + PERIODS  # how many periods of demand should we have inventory for
                inventory = self.schedule[f"{p}: Inventory"][i]
                demand = forecast[p]["Value"][i:look_ahead].sum()
                run_out.append(inventory / demand)

            # get the minimum run out rate
            idx = np.argmin(run_out)
            if run_out[idx] < 1:
                scheduled_product = self.products[idx]
            else:  # there's enough inventory to satisfy the upcoming demand
                scheduled_product = "None"

            # satisfy this period's demand and produce product
            schedule = pd.DataFrame({"Period": [i + 1], "Production": [scheduled_product]})
            for p in self.products:
                if p == scheduled_product:
                    production = production_rate[p]
                else:
                    production = 0

                schedule[f"{p}: Demand"] = forecast[p]["Value"][i]
                schedule[f"{p}: Inventory"] = max(0, production + self.schedule[f"{p}: Inventory"][i] - forecast[p]["Value"][i])
                schedule[f"{p}: Demand Satisfaction"] = min(1, (production + self.schedule[f"{p}: Inventory"][i]) / forecast[p]["Value"][i])

            self.schedule = pd.concat([self.schedule, schedule], axis="index").reset_index(drop=True)

        # compute expected demand satisfaction for each product
        satisfaction = list()
        for p in self.products:
            satisfaction.append(self.schedule[f"{p}: Demand Satisfaction"].mean())

        self.demand_satisfaction = pd.DataFrame({
            "Product": self.products,
            "Demand Satisfaction": satisfaction,
        })

    def plots(self):
        # plot inventory levels over time
        for p in self.products:
            self.line_plot(
                self.schedule,
                x="Period",
                y=f"{p}: Inventory",
                title=f"{p}: Inventory Levels Over Time",
                font_size=16,
            )

        # plot demand satisfaction over time
        for p in self.products:
            self.bar_plot(
                self.schedule,
                x="Period",
                y=f"{p}: Demand Satisfaction",
                title=f"{p}: Demand Satisfaction Over Time",
                font_size=16,
            )
        
        # plot the production schedule
        self.schedule[" "] = 1
        self.bar_plot(
            self.schedule,
            x="Period",
            y=" ",
            color="Production",
            title="Production Schedule",
            font_size=16,
        )
        self.schedule = self.schedule.drop(columns=" ")

    def line_plot(self, df, x, y, color=None, title="Line Plot", font_size=None):
        fig = px.line(df, x=x, y=y, color=color, title=title)
        fig.update_layout(font=dict(size=font_size))
        title = re.sub("[^A-Za-z0-9]+", "", title)
        plot(fig, filename=f"{title}.html")

    def bar_plot(self, df, x, y, color=None, title="Bar Plot", font_size=None):
        fig = px.bar(df, x=x, y=y, color=color, title=title)
        fig.update_layout(font=dict(size=font_size))
        title = re.sub("[^A-Za-z0-9]+", "", title)
        plot(fig, filename=f"{title}.html")
