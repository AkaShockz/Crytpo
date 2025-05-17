import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                            QComboBox, QTableWidget, QTableWidgetItem, QTextEdit,
                            QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
import pyqtgraph as pg
import pandas as pd
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from technical_analysis import TechnicalAnalyzer
from sentiment_analysis import SentimentAnalyzer
from signal_generator import SignalGenerator
import config

class CryptoTradingApp(QMainWindow):
    def __init__(self):
        print("Initializing CryptoTradingApp")
        super().__init__()
        self.setWindowTitle("Advanced Crypto Trading Assistant")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.data_fetcher = DataFetcher()
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.signal_generator = SignalGenerator()
        
        # Setup UI
        self.setup_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(config.SIGNAL_INTERVAL * 1000)  # Convert to milliseconds
        
        # Initial data load
        self.update_data()

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Create tabs
        self.setup_dashboard_tab(tabs)
        self.setup_analysis_tab(tabs)
        self.setup_portfolio_tab(tabs)
        self.setup_settings_tab(tabs)

    def setup_dashboard_tab(self, tabs):
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        
        # Market Overview
        market_group = QGroupBox("Market Overview")
        market_layout = QGridLayout()
        
        # Price displays
        self.price_labels = {}
        for i, symbol in enumerate(config.SYMBOLS):
            label = QLabel(f"{symbol}: Loading...")
            label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
            self.price_labels[symbol] = label
            market_layout.addWidget(label, i // 3, i % 3)
        
        market_group.setLayout(market_layout)
        layout.addWidget(market_group)
        
        # Active Signals
        signals_group = QGroupBox("Active Trading Signals")
        signals_layout = QVBoxLayout()
        
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(5)
        self.signals_table.setHorizontalHeaderLabels(["Symbol", "Signal", "Price", "Confidence", "Time"])
        signals_layout.addWidget(self.signals_table)
        
        signals_group.setLayout(signals_layout)
        layout.addWidget(signals_group)
        
        tabs.addTab(dashboard, "Dashboard")

    def setup_analysis_tab(self, tabs):
        analysis = QWidget()
        layout = QVBoxLayout(analysis)
        
        # Symbol Selection
        symbol_layout = QHBoxLayout()
        symbol_label = QLabel("Select Symbol:")
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(config.SYMBOLS)
        self.symbol_combo.currentTextChanged.connect(self.update_chart)
        symbol_layout.addWidget(symbol_label)
        symbol_layout.addWidget(self.symbol_combo)
        layout.addLayout(symbol_layout)
        
        # Chart
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground('w')
        layout.addWidget(self.chart_widget)
        
        # Technical Indicators
        indicators_group = QGroupBox("Technical Indicators")
        indicators_layout = QGridLayout()
        
        # RSI
        rsi_label = QLabel("RSI:")
        self.rsi_value = QLabel("--")
        indicators_layout.addWidget(rsi_label, 0, 0)
        indicators_layout.addWidget(self.rsi_value, 0, 1)
        
        # MACD
        macd_label = QLabel("MACD:")
        self.macd_value = QLabel("--")
        indicators_layout.addWidget(macd_label, 1, 0)
        indicators_layout.addWidget(self.macd_value, 1, 1)
        
        indicators_group.setLayout(indicators_layout)
        layout.addWidget(indicators_group)
        
        tabs.addTab(analysis, "Analysis")

    def setup_portfolio_tab(self, tabs):
        portfolio = QWidget()
        layout = QVBoxLayout(portfolio)
        
        # Portfolio Summary
        summary_group = QGroupBox("Portfolio Summary")
        summary_layout = QGridLayout()
        
        # Total Value
        total_label = QLabel("Total Value:")
        self.total_value = QLabel("$0.00")
        summary_layout.addWidget(total_label, 0, 0)
        summary_layout.addWidget(self.total_value, 0, 1)
        
        # 24h Change
        change_label = QLabel("24h Change:")
        self.change_value = QLabel("0.00%")
        summary_layout.addWidget(change_label, 1, 0)
        summary_layout.addWidget(self.change_value, 1, 1)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Holdings Table
        holdings_group = QGroupBox("Holdings")
        holdings_layout = QVBoxLayout()
        
        self.holdings_table = QTableWidget()
        self.holdings_table.setColumnCount(5)
        self.holdings_table.setHorizontalHeaderLabels(["Symbol", "Amount", "Value", "24h Change", "Allocation"])
        holdings_layout.addWidget(self.holdings_table)
        
        holdings_group.setLayout(holdings_layout)
        layout.addWidget(holdings_group)
        
        tabs.addTab(portfolio, "Portfolio")

    def setup_settings_tab(self, tabs):
        settings = QWidget()
        layout = QVBoxLayout(settings)
        
        # Trading Parameters
        trading_group = QGroupBox("Trading Parameters")
        trading_layout = QGridLayout()
        
        # RSI Settings
        rsi_period_label = QLabel("RSI Period:")
        self.rsi_period = QSpinBox()
        self.rsi_period.setRange(2, 50)
        self.rsi_period.setValue(config.RSI_PERIOD)
        trading_layout.addWidget(rsi_period_label, 0, 0)
        trading_layout.addWidget(self.rsi_period, 0, 1)
        
        # MACD Settings
        macd_fast_label = QLabel("MACD Fast Period:")
        self.macd_fast = QSpinBox()
        self.macd_fast.setRange(2, 50)
        self.macd_fast.setValue(config.MACD_FAST)
        trading_layout.addWidget(macd_fast_label, 1, 0)
        trading_layout.addWidget(self.macd_fast, 1, 1)
        
        trading_group.setLayout(trading_layout)
        layout.addWidget(trading_group)
        
        # Save Button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        tabs.addTab(settings, "Settings")

    def update_data(self):
        """Update all data displays"""
        try:
            # Update prices
            for symbol in config.SYMBOLS:
                try:
                    price = self.data_fetcher.get_current_price(symbol)
                    self.price_labels[symbol].setText(f"{symbol}: ${price:,.2f}")
                except Exception as e:
                    self.price_labels[symbol].setText(f"{symbol}: Error")
            
            # Update signals
            self.update_signals()
            
            # Update chart if visible
            if self.symbol_combo.currentText():
                self.update_chart(self.symbol_combo.currentText())
                
        except Exception as e:
            print(f"Error updating data: {str(e)}")

    def update_signals(self):
        """Update trading signals table"""
        self.signals_table.setRowCount(0)
        
        for symbol in config.SYMBOLS:
            try:
                # Get current price
                current_price = self.data_fetcher.get_current_price(symbol)
                
                # Get historical data
                df = self.data_fetcher.get_historical_klines(symbol, '1h')
                
                # Get technical indicators
                rsi = self.technical_analyzer.calculate_rsi(df)
                macd = self.technical_analyzer.calculate_macd(df)
                
                # Get news sentiment
                news = self.data_fetcher.get_crypto_news(symbol)
                news_sentiment = self.sentiment_analyzer.analyze_news(news)
                
                # Generate signal
                signal = self.signal_generator.generate_signal(
                    symbol, current_price, rsi, macd, news_sentiment
                )
                
                if signal:
                    row = self.signals_table.rowCount()
                    self.signals_table.insertRow(row)
                    self.signals_table.setItem(row, 0, QTableWidgetItem(symbol))
                    self.signals_table.setItem(row, 1, QTableWidgetItem(signal['type']))
                    self.signals_table.setItem(row, 2, QTableWidgetItem(f"${current_price:,.2f}"))
                    self.signals_table.setItem(row, 3, QTableWidgetItem(f"{signal['confidence']:.2%}"))
                    self.signals_table.setItem(row, 4, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
                    
            except Exception as e:
                print(f"Error updating signals for {symbol}: {str(e)}")

    def update_chart(self, symbol):
        """Update price chart for selected symbol"""
        try:
            # Clear previous chart
            self.chart_widget.clear()
            
            # Get historical data
            df = self.data_fetcher.get_historical_klines(symbol, '1h')
            
            # Plot price
            self.chart_widget.plot(df.index, df['close'], name='Price', pen='b')
            
            # Add technical indicators
            rsi = self.technical_analyzer.calculate_rsi(df)
            macd = self.technical_analyzer.calculate_macd(df)
            
            # Update indicator values
            self.rsi_value.setText(f"{rsi[-1]:.2f}")
            self.macd_value.setText(f"{macd['macd'][-1]:.2f}")
            
        except Exception as e:
            print(f"Error updating chart: {str(e)}")

    def save_settings(self):
        """Save trading parameters"""
        try:
            # Update config
            config.RSI_PERIOD = self.rsi_period.value()
            config.MACD_FAST = self.macd_fast.value()
            
            # Reinitialize analyzers
            self.technical_analyzer = TechnicalAnalyzer()
            
            print("Settings saved successfully")
            
        except Exception as e:
            print(f"Error saving settings: {str(e)}")

def main():
    print("Starting GUI main()")
    try:
        app = QApplication(sys.argv)
        print("QApplication created")
        window = CryptoTradingApp()
        print("CryptoTradingApp created")
        window.show()
        print("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Exception in main: {e}")
        import traceback
        traceback.print_exc() 