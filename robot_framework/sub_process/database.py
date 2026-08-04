"""This module contains functions for querying the database."""

from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache

import pyodbc

from robot_framework import config


@dataclass(frozen=True)
class Employee:
    """An employee to potentially handle."""
    cpr: str
    overenskomst: str
    loenklasse: str
    ansaetteles_id: str


def get_employee_list(connection: pyodbc.Connection) -> list[Employee]:
    """Get the list of employees to potentially handle."""
    cut_off_date = date.today() - timedelta(days=config.LOOK_BACK_DAYS)
    cut_off_date = max(cut_off_date, config.GLOBAL_CUTOFF_DATE)

    cursor = connection.execute(
        """
        SELECT CPR, Overenskomst, Lønklasse, AnsættelsesID
        FROM [Personale].[sd_magistrat].[Ansættelse_alle]
        WHERE
            [deltidsbeskæftigelseskode] IN (2, 6)
            AND [Aktuel]='1'
            AND [Statuskode] = '1'
            AND [tjenestenummer] NOT LIKE 'e%'
            AND [institutionskode] <> 'XX'
            AND [SDUdtræksdato] > ?
        """,
        cut_off_date
    )

    return [Employee(cpr, overenskomst, loenklasse, ansaetteles_id) for cpr, overenskomst, loenklasse, ansaetteles_id in cursor.fetchall()]


def get_pension_rates(connection: pyodbc.Connection) -> dict[(str, str), bool]:
    """Get all pension rates for all overenskomster in the database.
    Returns a dictionary with overenskomst and løntrin as key and
    a bool of whether the rate is larger than 0 as value.
    """
    cursor = connection.execute(
        """
        SELECT DISTINCT Overenskomstnummer, Lønklasse, IIF(Samlet_pensionsprocent = 0, 0, 1)
        FROM [Personale].[sd].[Overenskomst_Kartotek]
        """
    )

    return {(row[0], row[1]): bool(row[3]) for row in cursor}


def get_expirering_employees(connection: pyodbc.Connection) -> list[tuple[str]]:
    """Get a list of employees that still cannot be handled but are about to leave the robot's
    working window."""
    warning_date = date.today() - timedelta(days=config.WARNING_DAYS)
    cut_off_date = date.today() - timedelta(days=config.LOOK_BACK_DAYS)

    warning_date = max(warning_date, config.GLOBAL_CUTOFF_DATE)
    cut_off_date = max(cut_off_date, config.GLOBAL_CUTOFF_DATE)

    if warning_date == cut_off_date:
        return []

    cursor = connection.execute(
        """
        SELECT AnsættelsesID
        FROM [Personale].[sd_magistrat].[Ansættelse_alle]
        WHERE
            [deltidsbeskæftigelseskode] IN (2, 6)
            AND [Aktuel]='1'
            AND [Statuskode] = '0'
            AND [tjenestenummer] NOT LIKE 'e%'
            AND [institutionskode] <> 'XX'
            AND [SDUdtræksdato] BETWEEN ? AND ?
        """,
        cut_off_date,
        warning_date
    )

    return [r[0] for r in cursor.fetchall()]
