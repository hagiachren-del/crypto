#!/bin/bash

#################################################
# Autonomous AI Trader - Startup Script
#
# This script starts the autonomous trading bot
# with safety checks and monitoring
#################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

CONFIG_FILE="config/autonomous.yml"
SECRETS_FILE="config/secrets.yml"
LOG_DIR="logs"
VENV_DIR="venv"

#################################################
# Helper Functions
#################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         AUTONOMOUS AI CRYPTOCURRENCY TRADER                    ║"
    echo "║         Powered by DeepSeek AI & MEXC Exchange                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

#################################################
# Pre-flight Checks
#################################################

check_dependencies() {
    print_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    print_success "pip3 found"
}

check_configuration() {
    print_info "Checking configuration..."

    # Check config file
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    print_success "Configuration file found"

    # Check secrets file
    if [ ! -f "$SECRETS_FILE" ]; then
        print_error "Secrets file not found: $SECRETS_FILE"
        print_info "Please copy config/secrets.example.yml to config/secrets.yml"
        print_info "and add your API keys"
        exit 1
    fi
    print_success "Secrets file found"

    # Verify secrets file has required keys
    if ! grep -q "deepseek:" "$SECRETS_FILE"; then
        print_error "DeepSeek API key not found in secrets.yml"
        exit 1
    fi

    if ! grep -q "mexc:" "$SECRETS_FILE"; then
        print_error "MEXC API keys not found in secrets.yml"
        exit 1
    fi

    print_success "API keys configured"
}

check_api_keys() {
    print_info "Validating API keys..."

    # Extract DeepSeek API key
    DEEPSEEK_KEY=$(grep -A 1 "deepseek:" "$SECRETS_FILE" | grep "api_key:" | cut -d'"' -f2 | tr -d ' ')

    if [ -z "$DEEPSEEK_KEY" ] || [ "$DEEPSEEK_KEY" == "your_deepseek_api_key_here" ]; then
        print_error "Invalid DeepSeek API key in secrets.yml"
        print_info "Get your API key from: https://platform.deepseek.com/"
        exit 1
    fi

    # Extract MEXC API keys
    MEXC_KEY=$(grep -A 2 "mexc:" "$SECRETS_FILE" | grep "api_key:" | cut -d'"' -f2 | tr -d ' ')

    if [ -z "$MEXC_KEY" ] || [ "$MEXC_KEY" == "your_mexc_api_key_here" ]; then
        print_error "Invalid MEXC API key in secrets.yml"
        print_info "Get your API keys from: https://www.mexc.com/user/openapi"
        exit 1
    fi

    print_success "API keys validated"
}

setup_environment() {
    print_info "Setting up environment..."

    # Create directories
    mkdir -p "$LOG_DIR"
    mkdir -p "data"
    mkdir -p "reports"

    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_warning "Virtual environment not found. Creating..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Install/update requirements
    print_info "Checking Python packages..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    print_success "Python packages ready"
}

display_trading_mode() {
    # Extract trading mode from config
    MODE=$(grep "^mode:" "$CONFIG_FILE" | cut -d' ' -f2)

    echo ""
    echo "════════════════════════════════════════════════════════════════"

    if [ "$MODE" == "paper" ]; then
        echo -e "${GREEN}TRADING MODE: PAPER TRADING (SIMULATION)${NC}"
        echo "No real money will be used. This is safe for testing."
    elif [ "$MODE" == "live" ]; then
        echo -e "${RED}TRADING MODE: LIVE TRADING (REAL MONEY)${NC}"
        echo -e "${RED}WARNING: This will use REAL funds from your MEXC account!${NC}"
    else
        echo -e "${YELLOW}TRADING MODE: $MODE (UNKNOWN)${NC}"
    fi

    echo "════════════════════════════════════════════════════════════════"
    echo ""
}

confirm_start() {
    MODE=$(grep "^mode:" "$CONFIG_FILE" | cut -d' ' -f2)

    if [ "$MODE" == "live" ]; then
        echo -e "${RED}"
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║                    ⚠️  LIVE TRADING WARNING  ⚠️                  ║"
        echo "║                                                                ║"
        echo "║  You are about to start LIVE trading with REAL money!         ║"
        echo "║                                                                ║"
        echo "║  Risks:                                                        ║"
        echo "║  • You may lose money                                          ║"
        echo "║  • Markets are volatile and unpredictable                      ║"
        echo "║  • AI decisions may not always be profitable                   ║"
        echo "║  • Technical issues may cause unexpected behavior              ║"
        echo "║                                                                ║"
        echo "║  Only proceed if:                                              ║"
        echo "║  ✓ You tested in paper mode successfully                       ║"
        echo "║  ✓ You understand the risks                                    ║"
        echo "║  ✓ You can afford to lose the capital                          ║"
        echo "║  ✓ You have emergency stop conditions configured               ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"

        read -p "Type 'START LIVE TRADING' to continue: " confirmation

        if [ "$confirmation" != "START LIVE TRADING" ]; then
            print_warning "Start cancelled by user"
            exit 0
        fi
    else
        read -p "Press ENTER to start autonomous trader (or Ctrl+C to cancel)... "
    fi
}

display_status() {
    echo ""
    print_info "System Status:"
    echo "  • Configuration: $CONFIG_FILE"
    echo "  • Trading Mode: $(grep "^mode:" "$CONFIG_FILE" | cut -d' ' -f2 | tr '[:lower:]' '[:upper:]')"
    echo "  • Symbols: $(grep -A 3 "^symbols:" "$CONFIG_FILE" | grep "  -" | cut -d'-' -f2 | tr '\n' ',' | sed 's/,$//' | tr -d ' ')"
    echo "  • Log Directory: $LOG_DIR"
    echo "  • Database: data/autonomous.db"
    echo ""
}

#################################################
# Main Execution
#################################################

main() {
    print_header

    # Run checks
    check_dependencies
    check_configuration
    check_api_keys
    setup_environment

    # Display information
    display_trading_mode
    display_status

    # Confirm start
    confirm_start

    # Start trader
    echo ""
    print_success "Starting Autonomous AI Trader..."
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "Press Ctrl+C to stop the trader gracefully"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    # Export API keys to environment (for DeepSeek)
    export DEEPSEEK_API_KEY=$(grep -A 1 "deepseek:" "$SECRETS_FILE" | grep "api_key:" | cut -d'"' -f2 | tr -d ' ')

    # Run the autonomous trader
    python3 scripts/autonomous_trader.py --config "$CONFIG_FILE"

    # Capture exit code
    EXIT_CODE=$?

    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        print_success "Autonomous trader stopped gracefully"
    else
        print_error "Autonomous trader stopped with error (exit code: $EXIT_CODE)"
    fi

    exit $EXIT_CODE
}

#################################################
# Script Entry Point
#################################################

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        print_header
        echo "Usage: ./start_autonomous_trader.sh [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --paper             Start in paper trading mode (override config)"
        echo "  --live              Start in live trading mode (override config)"
        echo "  --status            Show current status without starting"
        echo ""
        echo "Examples:"
        echo "  ./start_autonomous_trader.sh              # Start with config settings"
        echo "  ./start_autonomous_trader.sh --paper      # Force paper trading mode"
        echo "  ./start_autonomous_trader.sh --status     # Show status only"
        echo ""
        exit 0
        ;;
    --paper)
        # Override config to paper mode
        sed -i 's/^mode:.*/mode: paper/' "$CONFIG_FILE"
        main
        ;;
    --live)
        # Override config to live mode
        sed -i 's/^mode:.*/mode: live/' "$CONFIG_FILE"
        main
        ;;
    --status)
        print_header
        check_configuration
        display_status
        exit 0
        ;;
    "")
        # No arguments, run normally
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
