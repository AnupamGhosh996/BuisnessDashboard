import os
import re
import json
import statistics
from collections import defaultdict
from typing import Any, Optional
from backend.app.config import settings
from backend.app.services.data_loader import DataLoaderService

class AIAnalystService:
    @staticmethod
    def get_suggested_questions(columns: list[str]) -> list[str]:
        """Returns contextually relevant business questions for the dataset."""
        mappings = DataLoaderService.map_columns(columns)
        has_rev = "revenue" in mappings
        has_profit = "profit" in mappings
        has_prod = "product" in mappings
        has_reg = "region" in mappings
        has_date = "date" in mappings

        suggestions = []
        if has_rev:
            suggestions.append("What is the total revenue and average transaction value?")
        if has_profit:
            suggestions.append("Which category delivered the highest overall profit margin?")
        if has_prod and has_rev:
            suggestions.append("What are our top 5 revenue-generating products?")
        if has_reg:
            suggestions.append("How does business performance compare across regions?")
        if has_date and has_rev:
            suggestions.append("What are the monthly sales and revenue trajectories?")
        if has_prod and has_profit:
            suggestions.append("Which products or segments are underperforming in net profit?")
        suggestions.append("Provide an executive strategic summary of this dataset.")
        return suggestions[:6]

    @staticmethod
    def parse_and_compute(
        query: str,
        columns: list[str],
        rows: list[dict[str, Any]],
        mappings: dict[str, str]
    ) -> tuple[dict[str, Any], dict[str, Any], Optional[dict[str, Any]]]:
        """
        Safely interprets the user query and computes exact numerical metrics
        using strictly allowlisted, restricted analytical operations.
        Returns (query_plan, verified_metrics, chart_recommendation).
        """
        q_lower = query.lower()
        rev_col = mappings.get("revenue")
        profit_col = mappings.get("profit")
        cost_col = mappings.get("cost")
        prod_col = mappings.get("product")
        reg_col = mappings.get("region")
        cat_col = mappings.get("category")
        date_col = mappings.get("date")
        cust_col = mappings.get("customer")
        qty_col = mappings.get("quantity")

        def parse_float(val: Any) -> float:
            if val is None or str(val).strip() == "":
                return 0.0
            try:
                return float(str(val).replace("$", "").replace(",", ""))
            except ValueError:
                return 0.0

        query_plan = {
            "query": query,
            "operation": "general_overview",
            "target_metrics": [],
            "groupby": None,
            "filters_applied": {}
        }
        verified_metrics = {}
        chart_recommendation = None

        total_orders = len(rows)
        verified_metrics["total_records"] = total_orders

        # Calculate baseline metrics
        tot_rev = sum(parse_float(r.get(rev_col)) for r in rows) if rev_col else 0.0
        tot_profit = sum(parse_float(r.get(profit_col)) for r in rows) if profit_col else 0.0
        tot_cost = sum(parse_float(r.get(cost_col)) for r in rows) if cost_col else 0.0
        aov = tot_rev / total_orders if total_orders > 0 and rev_col else 0.0
        margin = (tot_profit / tot_rev * 100) if tot_rev > 0 and profit_col else 0.0

        # Case 1: Revenue & Overall Sales question
        if ("revenue" in q_lower or "sales" in q_lower or "turnover" in q_lower) and not any(k in q_lower for k in ["product", "region", "month", "trend", "underperforming"]):
            query_plan["operation"] = "aggregate_revenue"
            query_plan["target_metrics"] = ["total_revenue", "average_order_value"]
            verified_metrics["total_revenue"] = round(tot_rev, 2)
            verified_metrics["average_order_value"] = round(aov, 2)
            verified_metrics["total_orders"] = total_orders

        # Case 2: Profit, Margins, or Earnings
        elif ("profit" in q_lower or "margin" in q_lower or "earning" in q_lower) and not any(k in q_lower for k in ["product", "region", "underperforming"]):
            query_plan["operation"] = "aggregate_profit"
            query_plan["target_metrics"] = ["total_profit", "profit_margin", "total_revenue"]
            verified_metrics["total_profit"] = round(tot_profit, 2)
            verified_metrics["total_revenue"] = round(tot_rev, 2)
            verified_metrics["profit_margin_pct"] = round(margin, 2)

        # Case 3: Top Products / Product Performance
        elif "product" in q_lower or "item" in q_lower:
            query_plan["operation"] = "groupby_product"
            query_plan["groupby"] = prod_col
            prod_agg = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "orders": 0, "quantity": 0})
            for r in rows:
                p = str(r.get(prod_col) or "Unknown")
                prod_agg[p]["revenue"] += parse_float(r.get(rev_col)) if rev_col else 0.0
                prod_agg[p]["profit"] += parse_float(r.get(profit_col)) if profit_col else 0.0
                prod_agg[p]["orders"] += 1
                if qty_col:
                    prod_agg[p]["quantity"] += int(parse_float(r.get(qty_col)))

            # Check if asking for underperforming or lowest
            is_underperforming = any(w in q_lower for w in ["underperform", "lowest", "worst", "loss", "bottom", "least"])
            sorted_prods = sorted(prod_agg.items(), key=lambda x: x[1]["profit" if profit_col else "revenue"], reverse=(not is_underperforming))
            top_list = []
            for name, d in sorted_prods[:5]:
                top_list.append({
                    "product": name,
                    "revenue": round(d["revenue"], 2),
                    "profit": round(d["profit"], 2),
                    "orders": d["orders"],
                    "quantity": d["quantity"]
                })
            verified_metrics["ranked_products"] = top_list
            verified_metrics["ranking_type"] = "Lowest / Underperforming" if is_underperforming else "Top Performing"

            chart_recommendation = {
                "recommended": True,
                "chart_type": "bar",
                "title": f"{'Lowest Performing' if is_underperforming else 'Top'} Products by Profit",
                "x_key": "product",
                "y_key": "profit" if profit_col else "revenue",
                "data": top_list
            }

        # Case 4: Region Performance / Regional Comparison
        elif "region" in q_lower or "country" in q_lower or "geograph" in q_lower or "territory" in q_lower:
            query_plan["operation"] = "groupby_region"
            query_plan["groupby"] = reg_col
            reg_agg = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "orders": 0})
            for r in rows:
                reg = str(r.get(reg_col) or "Unknown")
                reg_agg[reg]["revenue"] += parse_float(r.get(rev_col)) if rev_col else 0.0
                reg_agg[reg]["profit"] += parse_float(r.get(profit_col)) if profit_col else 0.0
                reg_agg[reg]["orders"] += 1

            reg_list = []
            for name, d in sorted(reg_agg.items(), key=lambda x: x[1]["revenue"], reverse=True):
                m = (d["profit"] / d["revenue"] * 100) if d["revenue"] > 0 else 0.0
                reg_list.append({
                    "region": name,
                    "revenue": round(d["revenue"], 2),
                    "profit": round(d["profit"], 2),
                    "margin_pct": round(m, 1),
                    "orders": d["orders"]
                })
            verified_metrics["regional_performance"] = reg_list

            chart_recommendation = {
                "recommended": True,
                "chart_type": "bar",
                "title": "Revenue by Region",
                "x_key": "region",
                "y_key": "revenue",
                "data": reg_list
            }

        # Case 5: Monthly Sales Trends / Time-Series
        elif any(w in q_lower for w in ["month", "trend", "trajectory", "over time", "history"]):
            query_plan["operation"] = "timeseries_monthly"
            query_plan["groupby"] = date_col
            month_agg = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "orders": 0})
            for r in rows:
                d_val = r.get(date_col)
                if not d_val:
                    continue
                m_str = str(d_val)[:7]
                month_agg[m_str]["revenue"] += parse_float(r.get(rev_col)) if rev_col else 0.0
                month_agg[m_str]["profit"] += parse_float(r.get(profit_col)) if profit_col else 0.0
                month_agg[m_str]["orders"] += 1

            trend_list = []
            for m in sorted(month_agg.keys()):
                trend_list.append({
                    "period": m,
                    "revenue": round(month_agg[m]["revenue"], 2),
                    "profit": round(month_agg[m]["profit"], 2),
                    "orders": month_agg[m]["orders"]
                })
            verified_metrics["monthly_trends"] = trend_list

            # Check growth between first and last month
            if len(trend_list) >= 2:
                first_rev = trend_list[0]["revenue"]
                last_rev = trend_list[-1]["revenue"]
                growth = ((last_rev - first_rev) / first_rev * 100) if first_rev > 0 else 0.0
                verified_metrics["overall_period_growth_pct"] = round(growth, 1)

            chart_recommendation = {
                "recommended": True,
                "chart_type": "line",
                "title": "Monthly Revenue & Profit Trajectory",
                "x_key": "period",
                "y_key": "revenue",
                "data": trend_list
            }

        # Case 6: Category Breakdown
        elif "category" in q_lower or "segment" in q_lower or "department" in q_lower:
            query_plan["operation"] = "groupby_category"
            query_plan["groupby"] = cat_col
            cat_agg = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "orders": 0})
            for r in rows:
                c = str(r.get(cat_col) or "Unknown")
                cat_agg[c]["revenue"] += parse_float(r.get(rev_col)) if rev_col else 0.0
                cat_agg[c]["profit"] += parse_float(r.get(profit_col)) if profit_col else 0.0
                cat_agg[c]["orders"] += 1

            cat_list = []
            for name, d in sorted(cat_agg.items(), key=lambda x: x[1]["revenue"], reverse=True):
                m = (d["profit"] / d["revenue"] * 100) if d["revenue"] > 0 else 0.0
                cat_list.append({
                    "category": name,
                    "revenue": round(d["revenue"], 2),
                    "profit": round(d["profit"], 2),
                    "margin_pct": round(m, 1),
                    "orders": d["orders"]
                })
            verified_metrics["category_performance"] = cat_list

            chart_recommendation = {
                "recommended": True,
                "chart_type": "pie",
                "title": "Revenue Distribution by Category",
                "x_key": "category",
                "y_key": "revenue",
                "data": cat_list
            }

        # Case 7: Top Customers
        elif "customer" in q_lower or "client" in q_lower or "buyer" in q_lower:
            query_plan["operation"] = "groupby_customer"
            query_plan["groupby"] = cust_col
            cust_agg = defaultdict(lambda: {"revenue": 0.0, "orders": 0})
            for r in rows:
                c = str(r.get(cust_col) or "Unknown")
                cust_agg[c]["revenue"] += parse_float(r.get(rev_col)) if rev_col else 0.0
                cust_agg[c]["orders"] += 1

            cust_list = []
            for name, d in sorted(cust_agg.items(), key=lambda x: x[1]["revenue"], reverse=True)[:5]:
                cust_list.append({
                    "customer": name,
                    "revenue": round(d["revenue"], 2),
                    "orders": d["orders"]
                })
            verified_metrics["top_customers"] = cust_list

        # Default / Executive Summary fallback
        else:
            query_plan["operation"] = "executive_summary"
            verified_metrics["total_revenue"] = round(tot_rev, 2)
            verified_metrics["total_profit"] = round(tot_profit, 2)
            verified_metrics["profit_margin_pct"] = round(margin, 2)
            verified_metrics["total_orders"] = total_orders
            verified_metrics["average_order_value"] = round(aov, 2)

        return query_plan, verified_metrics, chart_recommendation

    @staticmethod
    def generate_response(
        query: str,
        columns: list[str],
        rows: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] = []
    ) -> dict[str, Any]:
        """
        Executes verified calculation and optionally calls Anthropic Claude API
        to craft an authoritative, mathematically grounded narrative.
        """
        mappings = DataLoaderService.map_columns(columns)
        query_plan, verified_metrics, chart_recommendation = AIAnalystService.parse_and_compute(
            query, columns, rows, mappings
        )

        api_key = os.getenv("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)
        is_live_ai = False
        answer_text = ""

        # Construct system prompt instructing Claude to ONLY cite verified calculations
        system_prompt = (
            "You are InsightIQ AI Data Analyst, an expert enterprise analytics consultant.\n"
            "STRICT RULES:\n"
            "1. ONLY reference and discuss the EXACT numbers provided in the 'Verified Computational Metrics' section below.\n"
            "2. NEVER invent, hallucinate, or estimate any numbers that are not in the verified payload.\n"
            "3. Format your response cleanly using GitHub Markdown with bold numbers, structured bullet points, and strategic executive insights.\n"
            "4. Conclude with 1-2 concrete, high-impact business recommendations based on these findings."
        )

        context_payload = {
            "user_query": query,
            "query_plan": query_plan,
            "verified_metrics": verified_metrics
        }

        # Attempt to call Anthropic Claude API if key is present
        if api_key and api_key.startswith("sk-ant-"):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)

                messages = []
                for hist in conversation_history[-4:]:
                    messages.append({"role": hist["role"], "content": hist["content"]})

                prompt_content = (
                    f"User question: {query}\n\n"
                    f"Verified Computational Metrics:\n```json\n{json.dumps(context_payload, indent=2)}\n```\n\n"
                    "Provide a professional, executive response explaining these findings."
                )
                messages.append({"role": "user", "content": prompt_content})

                response = client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=messages
                )
                answer_text = response.content[0].text
                is_live_ai = True
            except Exception as e:
                # If Claude API call errors (e.g. invalid key or network block), gracefully fall back
                answer_text = AIAnalystService._deterministic_narrative(query, query_plan, verified_metrics)
        else:
            # Deterministic calculation-backed generator
            answer_text = AIAnalystService._deterministic_narrative(query, query_plan, verified_metrics)

        # Suggested follow-ups
        follow_ups = []
        op = query_plan.get("operation", "")
        if "revenue" in op:
            follow_ups = ["Which region contributed the highest revenue?", "What are our top 5 products by revenue?"]
        elif "profit" in op:
            follow_ups = ["Which products have the lowest profit margin?", "Show profit breakdown by region."]
        elif "product" in op:
            follow_ups = ["What are the monthly trends for these products?", "Compare profit margins across categories."]
        elif "region" in op:
            follow_ups = ["What is the top product in each region?", "Show revenue over time for the leading region."]
        else:
            follow_ups = ["What are the top 5 products?", "Show regional sales distribution.", "Are there any anomalies detected?"]

        return {
            "answer": answer_text,
            "query_plan": query_plan,
            "verified_metrics": verified_metrics,
            "chart_recommendation": chart_recommendation,
            "suggested_follow_ups": follow_ups,
            "is_live_ai": is_live_ai
        }

    @staticmethod
    def _deterministic_narrative(query: str, query_plan: dict[str, Any], metrics: dict[str, Any]) -> str:
        """High-precision, calculation-backed narrative generator."""
        op = query_plan.get("operation", "")
        parts = []

        if op == "aggregate_revenue":
            rev = metrics.get("total_revenue", 0.0)
            aov = metrics.get("average_order_value", 0.0)
            orders = metrics.get("total_orders", 0)
            parts.append(f"### Revenue Performance Analysis\n")
            parts.append(f"Based on **{orders:,}** transactions recorded in the dataset:\n")
            parts.append(f"- **Total Revenue**: **${rev:,.2f}**")
            parts.append(f"- **Average Order Value (AOV)**: **${aov:,.2f}** per transaction")
            parts.append(f"- **Total Order Volume**: **{orders:,}** orders\n")
            parts.append("**Executive Takeaway**: Transaction values demonstrate consistent commercial traction. Focus on cross-selling to elevate AOV beyond current benchmarks.")

        elif op == "aggregate_profit":
            profit = metrics.get("total_profit", 0.0)
            rev = metrics.get("total_revenue", 0.0)
            margin = metrics.get("profit_margin_pct", 0.0)
            parts.append(f"### Profitability & Margin Overview\n")
            parts.append(f"- **Total Net Profit**: **${profit:,.2f}**")
            parts.append(f"- **Gross Revenue**: **${rev:,.2f}**")
            parts.append(f"- **Overall Profit Margin**: **{margin:.2f}%**\n")
            parts.append(f"**Key Finding**: A healthy margin of **{margin:.1f}%** indicates sustainable unit economics. To scale profit, protect pricing power on high-volume lines.")

        elif op == "groupby_product":
            ranked = metrics.get("ranked_products", [])
            rtype = metrics.get("ranking_type", "Top Performing")
            parts.append(f"### {rtype} Products\n")
            parts.append(f"Identified the top products sorted by net contribution:\n")
            for idx, p in enumerate(ranked, 1):
                parts.append(f"{idx}. **{p['product']}**: **${p['revenue']:,.2f}** revenue | **${p['profit']:,.2f}** profit ({p['orders']} orders, {p['quantity']} units)")
            parts.append(f"\n**Strategic Recommendation**: Allocate marketing budget toward the top 2 products while reviewing cost structures for underperforming items.")

        elif op == "groupby_region":
            regs = metrics.get("regional_performance", [])
            parts.append(f"### Regional Performance Comparison\n")
            for r in regs:
                parts.append(f"- **{r['region']}**: **${r['revenue']:,.2f}** revenue | **${r['profit']:,.2f}** profit (**{r['margin_pct']}%** margin, {r['orders']} orders)")
            if regs:
                top_r = regs[0]
                parts.append(f"\n**Geographic Insight**: **{top_r['region']}** leads all territories with **${top_r['revenue']:,.2f}** in sales.")

        elif op == "timeseries_monthly":
            trends = metrics.get("monthly_trends", [])
            growth = metrics.get("overall_period_growth_pct")
            parts.append(f"### Monthly Performance Trajectory\n")
            parts.append(f"Tracking sales performance across **{len(trends)}** operational periods:")
            for t in trends[-6:]:  # show recent 6 months
                parts.append(f"- **{t['period']}**: **${t['revenue']:,.2f}** revenue | **${t['profit']:,.2f}** profit ({t['orders']} orders)")
            if growth is not None:
                parts.append(f"\n**Growth Trajectory**: Revenue evolved by **{growth:+.1f}%** from initial to final period.")

        elif op == "groupby_category":
            cats = metrics.get("category_performance", [])
            parts.append(f"### Category Segment Analysis\n")
            for c in cats:
                parts.append(f"- **{c['category']}**: **${c['revenue']:,.2f}** revenue | **${c['profit']:,.2f}** profit (**{c['margin_pct']}%** margin)")
            if cats:
                parts.append(f"\n**Portfolio Mix**: The **{cats[0]['category']}** segment generates the highest dollar volume.")

        elif op == "groupby_customer":
            custs = metrics.get("top_customers", [])
            parts.append(f"### Key Customer Contribution\n")
            for idx, c in enumerate(custs, 1):
                parts.append(f"{idx}. **{c['customer']}**: **${c['revenue']:,.2f}** in purchases across **{c['orders']}** orders")
            parts.append(f"\n**Account Strategy**: Implement dedicated key account management for top accounts.")

        else:
            rev = metrics.get("total_revenue", 0.0)
            profit = metrics.get("total_profit", 0.0)
            margin = metrics.get("profit_margin_pct", 0.0)
            orders = metrics.get("total_orders", 0)
            parts.append(f"### Executive Dataset Summary\n")
            parts.append(f"Here is the high-level business status computed from active dataset records:")
            parts.append(f"- **Total Gross Revenue**: **${rev:,.2f}**")
            parts.append(f"- **Total Net Profit**: **${profit:,.2f}**")
            parts.append(f"- **Aggregate Margin**: **{margin:.2f}%**")
            parts.append(f"- **Order Volume**: **{orders:,}** transactions\n")
            parts.append("**Summary Insight**: Overall operational health is robust. Drill down into specific categories or regions to uncover targeted expansion opportunities.")

        return "\n".join(parts)
