# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
from typing import override

import httpx
from pydantic import BaseModel, RootModel

from .base import Tool, ToolCallArguments, ToolExecResult, ToolParameter


class LocReport(BaseModel):
    rel_file_path: Path
    func_name: str


class LocReports(RootModel):
    root: list[LocReport]

    @classmethod
    def as_tool_parameter(cls) -> ToolParameter:
        return ToolParameter(
            name="loc_reports",
            type="array",
            description="List of lines of location reports.",
            items=LocReport.model_json_schema(),
            required=True,
        )


class ReportLocsTool(Tool):
    """Tool to report location information for functions or code segments."""

    def __init__(self, model_provider: str | None = None) -> None:
        super().__init__(model_provider)

    @override
    def get_model_provider(self) -> str | None:
        return self._model_provider

    @override
    def get_name(self) -> str:
        return "report_locs"

    @override
    def get_description(self) -> str:
        return "Report the locations of functions or code segments in files. This tool helps track and document the location of important code elements."

    @override
    def get_parameters(self) -> list[ToolParameter]:
        return [LocReports.as_tool_parameter()]

    @override
    async def execute(self, arguments: ToolCallArguments) -> ToolExecResult:
        loc_reports_data = arguments.get("loc_reports", [])

        if not loc_reports_data:
            return ToolExecResult(error="No location reports provided.")

        try:
            # Validate the location reports data
            loc_reports = LocReports.model_validate(loc_reports_data)

            # Get the base URL from environment variable
            base_url = os.getenv("LOC_REPORT_URL")
            if not base_url:
                return ToolExecResult(error="LOC_REPORT_URL environment variable not set.")

            # Prepare the URL
            url = f"{base_url.rstrip('/')}/report"

            # Prepare the data to send
            data = {"loc_reports": [report.model_dump() for report in loc_reports.root]}

            # Send POST request
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()

            return ToolExecResult(output="Location reports sent successfully.")

        except httpx.HTTPError as e:
            return ToolExecResult(error=f"Failed to send location reports: {str(e)}")
        except Exception as e:
            return ToolExecResult(error=f"Error processing location reports: {str(e)}")
