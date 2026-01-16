"""Advanced analytics and visualization for trading results"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict
import warnings
warnings.filterwarnings('ignore')


class TradingAnalytics:
    """Comprehensive analytics and visualization for trading results"""

    def __init__(self):
        """Initialize analytics"""
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")

    def plot_equity_curve(self, equity_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Plot equity curve

        Args:
            equity_df: DataFrame with equity curve
            save_path: Path to save plot (optional)
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Equity curve
        ax1.plot(equity_df.index, equity_df['equity'], linewidth=2, label='Equity')
        ax1.fill_between(equity_df.index, equity_df['equity'], alpha=0.3)
        ax1.set_title('Portfolio Equity Curve', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Equity ($)', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Drawdown
        cumulative = equity_df['equity']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100

        ax2.fill_between(equity_df.index, drawdown, 0, alpha=0.3, color='red', label='Drawdown')
        ax2.plot(equity_df.index, drawdown, color='red', linewidth=1)
        ax2.set_title('Drawdown', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Equity curve saved to {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_returns_distribution(self, trades_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Plot returns distribution

        Args:
            trades_df: DataFrame with trades
            save_path: Path to save plot (optional)
        """
        closed_trades = trades_df[trades_df['type'] == 'close']

        if len(closed_trades) == 0:
            print("No closed trades to plot")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Returns histogram
        returns = closed_trades['pnl']
        ax1.hist(returns, bins=30, alpha=0.7, edgecolor='black')
        ax1.axvline(returns.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: ${returns.mean():.2f}')
        ax1.axvline(0, color='black', linestyle='-', linewidth=1)
        ax1.set_title('Trade Returns Distribution', fontsize=16, fontweight='bold')
        ax1.set_xlabel('PnL ($)', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Returns box plot
        ax2.boxplot(returns, vert=True)
        ax2.set_title('Returns Box Plot', fontsize=16, fontweight='bold')
        ax2.set_ylabel('PnL ($)', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Returns distribution saved to {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_monthly_returns(self, equity_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Plot monthly returns heatmap

        Args:
            equity_df: DataFrame with equity curve
            save_path: Path to save plot (optional)
        """
        if len(equity_df) == 0:
            print("No data to plot")
            return

        # Calculate monthly returns
        monthly_equity = equity_df['equity'].resample('M').last()
        monthly_returns = monthly_equity.pct_change() * 100

        # Create pivot table for heatmap
        monthly_returns_df = pd.DataFrame({
            'Year': monthly_returns.index.year,
            'Month': monthly_returns.index.month,
            'Return': monthly_returns.values
        })

        pivot = monthly_returns_df.pivot(index='Month', columns='Year', values='Return')

        # Plot heatmap
        fig, ax = plt.subplots(figsize=(12, 8))

        sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                    cbar_kws={'label': 'Return (%)'}, ax=ax)

        ax.set_title('Monthly Returns Heatmap', fontsize=16, fontweight='bold')
        ax.set_ylabel('Month', fontsize=12)
        ax.set_xlabel('Year', fontsize=12)

        # Set month labels
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_yticklabels(month_labels)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Monthly returns saved to {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_trade_analysis(self, trades_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Plot comprehensive trade analysis

        Args:
            trades_df: DataFrame with trades
            save_path: Path to save plot (optional)
        """
        closed_trades = trades_df[trades_df['type'] == 'close']

        if len(closed_trades) == 0:
            print("No closed trades to analyze")
            return

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

        # Cumulative PnL
        closed_trades['cumulative_pnl'] = closed_trades['pnl'].cumsum()
        ax1.plot(closed_trades.index, closed_trades['cumulative_pnl'], linewidth=2)
        ax1.fill_between(closed_trades.index, closed_trades['cumulative_pnl'], alpha=0.3)
        ax1.set_title('Cumulative PnL', fontsize=14, fontweight='bold')
        ax1.set_ylabel('PnL ($)', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Win/Loss ratio
        wins = closed_trades[closed_trades['pnl'] > 0]
        losses = closed_trades[closed_trades['pnl'] <= 0]

        labels = ['Wins', 'Losses']
        sizes = [len(wins), len(losses)]
        colors = ['green', 'red']

        ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90, textprops={'fontsize': 10})
        ax2.set_title('Win/Loss Ratio', fontsize=14, fontweight='bold')

        # Trade size distribution
        ax3.hist(closed_trades['quantity'], bins=20, alpha=0.7, edgecolor='black')
        ax3.set_title('Trade Size Distribution', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Quantity', fontsize=10)
        ax3.set_ylabel('Frequency', fontsize=10)
        ax3.grid(True, alpha=0.3)

        # PnL over time
        ax4.scatter(range(len(closed_trades)), closed_trades['pnl'],
                    c=closed_trades['pnl'], cmap='RdYlGn', alpha=0.6)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax4.set_title('Trade PnL Over Time', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Trade Number', fontsize=10)
        ax4.set_ylabel('PnL ($)', fontsize=10)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Trade analysis saved to {save_path}")
        else:
            plt.show()

        plt.close()

    def generate_report(self, equity_df: pd.DataFrame, trades_df: pd.DataFrame,
                        metrics: Dict, output_dir: str = 'reports'):
        """
        Generate comprehensive trading report with all visualizations

        Args:
            equity_df: DataFrame with equity curve
            trades_df: DataFrame with trades
            metrics: Dictionary with performance metrics
            output_dir: Output directory for reports
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        print(f"\nGenerating comprehensive trading report...")

        # Generate all plots
        self.plot_equity_curve(equity_df, f'{output_dir}/equity_curve.png')
        self.plot_returns_distribution(trades_df, f'{output_dir}/returns_distribution.png')
        self.plot_monthly_returns(equity_df, f'{output_dir}/monthly_returns.png')
        self.plot_trade_analysis(trades_df, f'{output_dir}/trade_analysis.png')

        # Save metrics to CSV
        metrics_df = pd.DataFrame([metrics]).T
        metrics_df.columns = ['Value']
        metrics_df.to_csv(f'{output_dir}/metrics.csv')

        # Save trades to CSV
        trades_df.to_csv(f'{output_dir}/trades.csv')

        # Save equity curve to CSV
        equity_df.to_csv(f'{output_dir}/equity_curve.csv')

        print(f"\nReport generated successfully in '{output_dir}/' directory")
        print(f"  - equity_curve.png")
        print(f"  - returns_distribution.png")
        print(f"  - monthly_returns.png")
        print(f"  - trade_analysis.png")
        print(f"  - metrics.csv")
        print(f"  - trades.csv")
        print(f"  - equity_curve.csv")
