"""This module contains the main process of the robot."""


from email.message import EmailMessage
import smtplib

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from OpenOrchestrator.database.queues import QueueStatus
import pyodbc

from robot_framework import config
from robot_framework.sub_process import database


# pylint: disable-next=unused-argument
def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    db_connection = pyodbc.connect("Server=FaellesSQL;Database=Personale;Trusted_Connection=yes;Driver={ODBC Driver 17 for SQL Server}")

    handle_employee_letters(orchestrator_connection, db_connection)
    handle_employee_warnings(orchestrator_connection, db_connection)


def handle_employee_letters(orchestrator_connection: OrchestratorConnection, db_connection: pyodbc.Connection):
    """Send letters to all part time employees that has status code 1.
    The letter is chosen based on whether the employee has pension
    as part of their overenskomst or not.

    If no overenskomst is found for the employee a warning is sent to HR.

    Use queue elements to limit to one letter per employee.
    """
    employees = database.get_employee_list(db_connection)
    pension_rates = database.get_pension_rates(db_connection)

    for employee in employees:
        # if orchestrator_connection.get_queue_elements(config.QUEUE_NAME, reference=employee.ansaetteles_id, status=QueueStatus.DONE):
        #     orchestrator_connection.log_trace(f"Skipping letter: {employee.ansaetteles_id}. Already handled")
        #     continue

        # qe = orchestrator_connection.create_queue_element(config.QUEUE_NAME, employee.ansaetteles_id)

        has_pension = pension_rates.get((employee.overenskomst, employee.loenklasse))

        if has_pension is None:
            send_no_overenskomst_warning(employee)
            # orchestrator_connection.set_queue_element_status(qe.id, QueueStatus.FAILED, message="Ingen overenskomst. Advarsel sendt.")
        else:
            send_letter(employee, has_pension)
            # orchestrator_connection.set_queue_element_status(qe.id, QueueStatus.DONE, message="Brev sendt.")


def send_letter(employee: database.Employee, has_pension: bool):
    # TODO: Send letter
    print(f"SENDING {employee.ansaetteles_id}, {has_pension}")


def send_warning_email(subject: str, body: str):
    """Send a warning email to HR with the robot's standard sender, receiver and signature."""
    msg = EmailMessage()
    msg['to'] = config.WARNINGS_RECEIVER
    msg['from'] = config.WARNINGS_SENDER
    msg['subject'] = subject

    msg.set_content(
        "Hejsa\n"
        f"{body}"
        "Venlig hilsen\n"
        "'Tilknytningsbreve til timelønnede'-robotten"
    )

    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.send_message(msg)


def send_no_overenskomst_warning(employee: database.Employee):
    """Send a warning email that no overenskomst could be found for the given employee."""
    send_warning_email(
        subject="Timelønnets overenskomst mangler i kartotek.",
        body=(
            f"Ansatte med id {employee.ansaetteles_id} står med overenskomstnummer {employee.overenskomst} lønklasse {employee.loenklasse}.\n"
            "Denne kunne ikke findes i overenskomstkartoteket.\n"
            "Tilknytningsbrev er derfor ikke blevet sendt.\n"
            "Hvis overenskomsten tilføjes inden de næste par dage, kan robotten stadig nå at behandle dem, "
            "ellers skal de behandles manuelt.\n"
        )
    )


def handle_employee_warnings(orchestrator_connection: OrchestratorConnection, db_connection: pyodbc.Connection):
    """Send warnings on all part time employees which status code is still 0 but are about to leave
    the robot's working window.

    Use queue elements to limit to one warning per employee.
    """
    expirering_employees = database.get_expirering_employees(db_connection)

    for employee_id in expirering_employees:
        if orchestrator_connection.get_queue_elements(config.QUEUE_NAME_WARNINGS, reference=employee_id, status=QueueStatus.DONE):
            orchestrator_connection.log_trace(f"Skipping warning: {employee_id}. Already handled")
            continue

        qe = orchestrator_connection.create_queue_element(config.QUEUE_NAME_WARNINGS, employee_id)

        send_expirery_warning(employee_id)

        orchestrator_connection.set_queue_element_status(qe.id, QueueStatus.DONE)


def send_expirery_warning(employee_id: str):
    """Send a warning email that the given employee is about to leave the robot's
    working window.
    """
    send_warning_email(
        subject="Timelønnet stadig ikke aktiv.",
        body=(
            f"Ansatte med id {employee_id} står stadig som inaktiv efter {config.WARNING_DAYS} dage.\n"
            "Tilknytningsbrev er derfor ikke blevet sendt.\n"
            "Hvis deres status ændres inden de næste par dage, kan robotten stadig nå at behandle dem, "
            "ellers skal de behandles manuelt.\n"
        )
    )



if __name__ == '__main__':
    import os
    import uuid
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Tilknytningsbreve test", conn_string, crypto_key, '', "", uuid.uuid4())
    process(oc)
