import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("DCF Valuation Tool (Robust Version)")

ticker = st.text_input("Enter Stock Ticker", "AAPL").strip().upper()

wacc = st.slider("WACC (%)", 5.0, 18.0, 10.0) / 100
growth_rate = st.slider("5-Year FCF Growth (%)", 0.0, 20.0, 5.0) / 100
terminal_growth = st.slider("Terminal Growth (%)", 0.0, 6.0, 2.5) / 100

forecast_years = 5

def pick_first_available(df: pd.DataFrame, candidates: list[str]):
    """Return the most recent value from the first matching row label in candidates."""
    if df is None or df.empty:
        return None
    for label in candidates:
        if label in df.index:
            # Most recent column is usually first, but safer to take first non-null across columns
            row = df.loc[label]
            for v in row.values:
                if pd.notna(v):
                    return float(v)
    return None

def safe_get(info: dict, key: str):
    v = info.get(key, None)
    try:
        return None if v is None else float(v)
    except Exception:
        return None

if ticker:
    stock = yf.Ticker(ticker)

    try:
        info = stock.info or {}
        cashflow = stock.cashflow
        balance_sheet = stock.balance_sheet

        # Shares
        shares = safe_get(info, "sharesOutstanding")
        if not shares or shares <= 0:
            st.error("Could not retrieve shares outstanding for this ticker.")
            st.stop()

        # --- Base Free Cash Flow (FCF) ---
        # Preferred: build from statements (CFO + CapEx)
        cfo = pick_first_available(
            cashflow,
            ["Total Cash From Operating Activities", "Operating Cash Flow"]
        )
        capex = pick_first_available(
            cashflow,
            ["Capital Expenditures", "Capital Expenditure"]
        )

        fcf = None
        if cfo is not None and capex is not None:
            # capex is usually negative in statements; CFO + CapEx works
            fcf = cfo + capex

        # Fallback: TTM free cash flow from info (often available)
        if fcf is None:
            fcf = safe_get(info, "freeCashflow")

        if fcf is None:
            st.error("Could not compute Free Cash Flow from yfinance data for this ticker.")
            st.write("Try a large-cap ticker like AAPL, MSFT, JNJ to confirm it works.")
            st.stop()

        # --- Debt and Cash for Equity bridge ---
        total_debt = (
            pick_first_available(balance_sheet, ["Total Debt"])
            or safe_get(info, "totalDebt")
        )

        cash = (
            pick_first_available(balance_sheet, ["Cash", "Cash And Cash Equivalents"])
            or safe_get(info, "totalCash")
        )

        # If debt/cash missing, treat as 0 rather than hard-fail
        total_debt = 0.0 if total_debt is None else total_debt
        cash = 0.0 if cash is None else cash

        # --- Forecast FCF ---
        fcf_forecast = [fcf * (1 + growth_rate) ** year for year in range(1, forecast_years + 1)]

        # --- Discount FCF ---
        discounted_fcf = [fcf_forecast[i] / (1 + wacc) ** (i + 1) for i in range(forecast_years)]

        # --- Terminal value (Gordon Growth) ---
        if wacc <= terminal_growth:
            st.error("WACC must be greater than Terminal Growth for the Gordon Growth formula.")
            st.stop()

        terminal_value = (fcf_forecast[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
        discounted_terminal_value = terminal_value / (1 + wacc) ** forecast_years

        enterprise_value = sum(discounted_fcf) + discounted_terminal_value
        equity_value = enterprise_value - total_debt + cash
        per_share = equity_value / shares

        # --- Display outputs ---
        st.subheader("Key Outputs")
        st.metric("Enterprise Value (EV)", f"${enterprise_value:,.0f}")
        st.metric("Equity Value", f"${equity_value:,.0f}")
        st.metric("Intrinsic Value / Share", f"${per_share:,.2f}")

        st.caption(
            f"Base FCF used: ${fcf:,.0f} (from statements if available; otherwise TTM freeCashflow from yfinance info)."
        )

        # --- Sensitivity: WACC x Terminal Growth ---
        st.subheader("Sensitivity Analysis (WACC × Terminal Growth)")

        wacc_vals = np.round(np.linspace(max(0.05, wacc - 0.02), wacc + 0.02, 5), 4)
        tg_vals = np.round(np.linspace(max(0.00, terminal_growth - 0.01), terminal_growth + 0.01, 5), 4)

        sens = pd.DataFrame(
            index=[f"{w*100:.2f}%" for w in wacc_vals],
            columns=[f"{g*100:.2f}%" for g in tg_vals]
        )

        for w in wacc_vals:
            for g in tg_vals:
                if w <= g:
                    sens.loc[f"{w*100:.2f}%", f"{g*100:.2f}%"] = "N/A"
                    continue
                tv = (fcf_forecast[-1] * (1 + g)) / (w - g)
                d_tv = tv / (1 + w) ** forecast_years
                ev = sum(discounted_fcf) + d_tv
                eq = ev - total_debt + cash
                price = eq / shares
                sens.loc[f"{w*100:.2f}%", f"{g*100:.2f}%"] = round(price, 2)

        st.dataframe(sens, use_container_width=True)

    except Exception as e:
        st.error("Something went wrong while pulling data or running the model.")
        st.write("Technical details (for debugging):")
        st.code(str(e))
