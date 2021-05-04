# Copyright 2021 ForgeFlow S.L.  <https://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def update_follow_recurrence_field(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE calendar_event ce
        SET follow_recurrence = True
        WHERE recurrency = True
        """,
    )


def map_calendar_event_byday(env):
    openupgrade.map_values(
        env.cr,
        openupgrade.get_legacy_name("byday"),
        "byday",
        [("5", "-1")],
        table="calendar_event",
    )


def fill_calendar_recurrence_table(env):
    openupgrade.logged_query(
        env.cr,
        """
        WITH recur AS (
            INSERT INTO calendar_recurrence (base_event_id,
                event_tz,rrule,rrule_type,end_type,interval,count,
                mo,tu,we,th,fr,sa,su,month_by,day,weekday,byday,until,
                create_uid,create_date,write_uid,write_date)
            SELECT id,event_tz,rrule,rrule_type,end_type,interval,count,
                mo,tu,we,th,fr,sa,su,month_by,day,week_list,byday,final_date,
                create_uid,create_date,write_uid,write_date)
            FROM calendar_event
            WHERE recurrency AND recurrence_id IS NULL
                AND (recurrent_id IS NULL OR recurrent_id = '')
            RETURNING id,base_event_id
        )
        UPDATE calendar_event ce
        SET recurrence_id = recur.id
        FROM recur
        WHERE recur.base_event_id = ce.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE calendar_event ce
        SET recurrence_id = ce2.recurrence_id
        FROM calendar_event ce2
        WHERE ce.recurrency AND ce.recurrence_id IS NULL
            AND ce.recurrent_id = ce2.id || ''
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    update_follow_recurrence_field(env)
    map_calendar_event_byday(env)
    fill_calendar_recurrence_table(env)
    openupgrade.load_data(env.cr, "calendar", "14.0.1.0/noupdate_changes.xml")
