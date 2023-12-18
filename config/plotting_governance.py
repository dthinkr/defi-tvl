import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pygini import gini
import matplotlib.dates as mdates

class TokenDistributionVisualizer:
    def __init__(self, csv_path, palette='plasma'):
        self.df_agg = pd.read_csv(csv_path)
        self.palette = sns.color_palette(palette, n_colors=10)  # Adjust number of colors as needed
        self.prepare_data()

    def prepare_data(self):
        self.pivot_data = self.df_agg.pivot_table(index='timeStamp', columns='user_address', values='cumulative_stake', aggfunc='sum', fill_value=0)
        self.pivot_data = self.pivot_data.cumsum()

    def calculate_gini_coefficients(self):
        def calculate_gini(df):
            if df.empty:
                return 0
            return gini(df.values)

        self.gini_coefficients = self.pivot_data.apply(calculate_gini, axis=1)

    def plot_gini_coefficients(self):
        # Ensure the index is a DateTimeIndex using the correct string format for your dates
        if not isinstance(self.gini_coefficients.index, pd.DatetimeIndex):
            self.gini_coefficients.index = pd.to_datetime(self.gini_coefficients.index, format='%Y-%m-%d')  # adjust format if needed

        # Now plot using the corrected index
        plt.figure(figsize=(12, 6), dpi=100)
        plt.plot(self.gini_coefficients.index, self.gini_coefficients.values, label='Gini Coefficient', color=self.palette[0])
        plt.xlabel('Date')
        plt.ylabel('Gini Coefficient')
        plt.title('Gini Coefficient Over Time')
        plt.legend()
        plt.grid(True)
        plt.show()

    def aggregate_top_addresses(self, top_n=5):
        top_addresses = self.pivot_data.columns[:top_n]
        other_addresses = self.pivot_data.columns[top_n:]
        self.pivot_data['Other'] = self.pivot_data[other_addresses].sum(axis=1)
        self.pivot_data = self.pivot_data[top_addresses.tolist() + ['Other']]
        self.pivot_data.index = pd.to_datetime(self.pivot_data.index)

    def plot_staked_tokens(self):
        plt.figure(figsize=(12, 6), dpi=100)

        # Map each address to a color from the palette
        colors = {address: self.palette[i % len(self.palette)] for i, address in enumerate(self.pivot_data.columns)}

        # Create the stackplot using the colors dictionary
        plt.stackplot(self.pivot_data.index, self.pivot_data.T, labels=self.pivot_data.columns, 
                    colors=[colors[address] for address in self.pivot_data.columns], edgecolor='none')

        plt.title('Staked Tokens Over Time')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Stake')
        plt.legend(loc='upper left')
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gcf().autofmt_xdate()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


    def plot_yearly_distribution(self):
        self.df_agg['Year'] = pd.to_datetime(self.df_agg['timeStamp']).dt.year
        yearly_data = self.df_agg.groupby(['user_address', 'Year'])['cumulative_stake'].last().reset_index()
        melted_yearly_data = yearly_data.melt(id_vars=['user_address', 'Year'], var_name='Type', value_name='Stake')
        plt.figure(figsize=(16, 12))
        palette = sns.color_palette(self.palette, n_colors=len(melted_yearly_data['Year'].unique()))
        self._plot_boxplot(melted_yearly_data, palette)
        self._plot_violinplot(melted_yearly_data, palette)
        self._plot_kde(yearly_data, palette)
        self._plot_histogram(yearly_data, palette)
        plt.tight_layout()
        plt.show()

    # Define helper methods for specific plots
    def _plot_boxplot(self, data, palette):
        ax1 = plt.subplot(2, 2, 1)
        sns.boxplot(x='Year', y='Stake', data=data, palette=palette)
        ax1.set_title('(a) Boxplot')
        ax1.set_yscale('log')

    def _plot_violinplot(self, data, palette):
        ax2 = plt.subplot(2, 2, 2)
        sns.violinplot(x='Year', y='Stake', data=data, palette=palette)
        ax2.set_title('(b) Violin plot')
        ax2.set_yscale('log')

    def _plot_kde(self, data, palette):
        ax3 = plt.subplot(2, 2, 3)
        sns.kdeplot(data=data, x='cumulative_stake', hue='Year', fill=True, palette=palette)
        ax3.set_title('(c) KDE plot')
        ax3.set_xscale('log')
        ax3.set_yscale('log')

    def _plot_histogram(self, data, palette):
        ax4 = plt.subplot(2, 2, 4)
        sns.histplot(data=data, x='cumulative_stake', hue='Year', element='step', fill=False, common_norm=False, common_bins=False, palette=palette)
        ax4.set_title('(d) Histogram')
        ax4.set_xscale('log')
        ax4.set_yscale('log')