# -*- coding: utf-8 -*-
"""
TradingAgents CLI
命令行入口
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="TradingAgents-OpenClaw - AI Trading Research System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a stock/crypto")
    analyze_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL, BTC)")
    analyze_parser.add_argument("--market", choices=["auto", "us", "a", "crypto"],
                               default="auto", help="Market type")
    
    # data command
    data_parser = subparsers.add_parser("data", help="Get market data")
    data_parser.add_argument("symbol", help="Stock symbol")
    data_parser.add_argument("--source", choices=["auto", "yfinance", "sina", "crypto"],
                           default="auto", help="Data source")
    
    # version command
    subparsers.add_parser("version", help="Show version")
    
    args = parser.parse_args()
    
    if args.command == "version":
        print("TradingAgents-OpenClaw v0.1.0")
    elif args.command == "analyze":
        print(f"Analyzing {args.symbol} (market: {args.market})...")
        # TODO: Implement analysis
        print("Not yet implemented")
    elif args.command == "data":
        print(f"Getting data for {args.symbol} from {args.source}...")
        # TODO: Implement data fetch
        print("Not yet implemented")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
