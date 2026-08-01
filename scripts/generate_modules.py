"""Generate week-by-week schedule for website from CSV file.

Use this to convert from the course calendar spreadsheet to modules that work
with the course website template. Only run it on the weeks that haven't
occurred yet, otherwise it'll erase any manual work. Run from the root
directory of this repo, **not** from the scripts folder.

Usage:
    generate_modules.py CSV_FILE

Examples:
    python scripts/generate_modules.py scripts/fa23.csv
"""

import numpy as np
import pandas as pd
from docopt import docopt
from yaml import dump

# Same-day display order: lectures/exams before deadlines.
EVENT_PRIORITY = {
    "Lecture": 0,
    "Exam": 1,
    "Discussion": 2,
    "Lab Due": 3,
    "Project Due": 4,
    "Canceled": 5,
}

# Project label + emoji (replaces trailing "__" placeholders in the CSV).
PROJECT_INFO = [
    ("Gradebook", "PROJ 1", "💯"),
    ("Loans", "PROJ 2", "💸"),
    ("Language Models", "PROJ 3", "🗣"),
    ("Data Science Lifecycle", "PROJ 4", "🔁"),
]


def generate_modules(csv_file):
    df = (
        pd.read_csv(csv_file)
        .pipe(ffill_weeks)
        .pipe(parse_dates)
        .pipe(melt_into_events)
        .pipe(mark_exams_and_canceled_lectures)
        .pipe(number_events)
        .pipe(order_events)
    )
    readings = pd.read_csv(csv_file).pipe(make_readings)
    df.pipe(write_into_module_files, readings=readings)


def ffill_weeks(df):
    cols = {"week": df["Week"].ffill(), "week_title": df["Week Title"].ffill()}
    return df.assign(**cols).drop(columns=["Week", "Week Title"])


def parse_dates(df):
    return df.assign(
        date=pd.to_datetime(df["Date"], format="%a %m/%d/%y")
    ).drop(columns=["Date"])


def melt_into_events(df: pd.DataFrame):
    return (
        df.melt(
            id_vars=["week", "week_title", "date"],
            value_vars=[
                "Lecture",
                "Discussion",
                "Lab Due",
                "Project Due",
            ],
            var_name="event_type",
            value_name="title",
        )
        .dropna(subset=["title", "date", "week"])
        .loc[lambda d: d["title"].astype(str).str.strip().ne("")]
        .assign(week=lambda df: df["week"].astype(int))
        .sort_values("date")
    )


def mark_exams_and_canceled_lectures(
    df, cancelled_prefix="NO ", exam_substring="Exam"
):
    canceled = df["title"].str.startswith(cancelled_prefix)
    exams = (df["event_type"] == "Lecture") & (
        df["title"].str.contains(exam_substring)
    )
    marked_events = (
        df["event_type"].mask(canceled, "Canceled").mask(exams, "Exam")
    )
    return df.assign(event_type=marked_events)


def _project_meta(title: str):
    """Return (event_number, title_with_emoji) for a project due title."""
    cleaned = title.strip().replace(" __", "").replace("__", "").strip()
    for keyword, number, emoji in PROJECT_INFO:
        if keyword in cleaned:
            if cleaned.endswith(emoji):
                return number, cleaned
            return number, f"{cleaned} {emoji}"
    # Legacy "Project N ..." titles
    match = pd.Series([cleaned]).str.extract(r"Project (\d+)")[0].iloc[0]
    if pd.notna(match):
        return f"PROJ {int(match)}", cleaned
    if "Final Project" in cleaned:
        return "FINAL PROJ", cleaned
    return "PROJ", cleaned


def number_events(df):
    # Number lectures from 1-N, labs from 1-N, projects from 1-N, etc.
    #
    # [1] Labs: Need to take out Lab 1, Lab 2, etc. from the title
    # [2] Projects: named projects (Gradebook, Loans, ...) or legacy Project N
    # [3] Lectures: Number from 1-N
    # [4] Discussions: Number from 1-N
    # [5] Exams: Don't number
    # [6] Canceled: Don't number
    df = df.copy()

    # [1] Labs
    lab_titles_split = df.query('event_type == "Lab Due"')["title"].str.split(
        ": "
    )
    lab_numbers = lab_titles_split.str[0].str.upper()
    lab_titles = lab_titles_split.str[1]
    df.loc[lab_titles.index, "title"] = lab_titles

    # [2] Projects
    proj_mask = df["event_type"] == "Project Due"
    proj_meta = df.loc[proj_mask, "title"].map(_project_meta)
    project_numbers = proj_meta.map(lambda x: x[0])
    df.loc[proj_mask, "title"] = proj_meta.map(lambda x: x[1])

    # [3] Lectures
    lecs = df.query('event_type == "Lecture"')
    lec_numbers = "LEC " + pd.Series(
        np.arange(len(lecs)) + 1, lecs.index
    ).astype(str)

    # [4] Discussions
    discs = df.query('event_type == "Discussion"')
    disc_numbers = "DISC " + pd.Series(
        np.arange(len(discs)) + 1, discs.index
    ).astype(str)

    # [5] Exams
    exam_numbers = df.query('event_type == "Exam"').assign(
        event_numbers="EXAM"
    )["event_numbers"]

    event_numbers = pd.concat(
        [
            lab_numbers,
            project_numbers,
            lec_numbers,
            disc_numbers,
            exam_numbers,
        ]
    )
    return df.assign(event_number=event_numbers)


def order_events(df):
    return (
        df.assign(
            _priority=df["event_type"].map(EVENT_PRIORITY).fillna(99)
        )
        .sort_values(["date", "_priority"], kind="mergesort")
        .drop(columns=["_priority"])
    )


def make_readings(df):
    df = df[["Lecture", "Readings"]].dropna()
    return dict(zip(df["Lecture"], df["Readings"]))


def write_into_module_files(
    df,
    readings={},
    event_type_as_css_class={
        "Lab Due": "lab",
        "Project Due": "proj",
        "Lecture": "lecture",
        "Discussion": "disc",
        "Exam": "exam",
        "Canceled": "canceled",
    },
):
    def make_days(events):
        return [
            (
                {
                    "name": e.event_number,
                    "type": event_type_as_css_class[e.event_type],
                    "title": e.title,
                    "reading": readings.get(e.title, ""),
                }
                if e.event_type != "Canceled"
                else {"markdown_content": e.title}
            )
            for e in events.itertuples(index=False)
        ]

    def write_week_module_file(week_df):
        week = int(week_df["week"].iloc[0])
        week_title = week_df["week_title"].iloc[0]
        date_events = week_df.groupby("date", sort=True).apply(
            make_days, include_groups=False
        )
        days = [
            {"date": date.strftime(r"%Y-%m-%d"), "events": events}
            for date, events in date_events.items()
        ]
        week_data = dump(
            {
                "title": f"Week {week} – {week_title}",
                "weekNumber": week,
                "days": days,
            },
            sort_keys=False,
            allow_unicode=True,
        )
        module_file_path = f"_modules/week-{week:02d}.md"
        with open(module_file_path, "w") as f:
            f.writelines(["---\n", week_data, "---\n"])
        print(f"Wrote: {module_file_path}")

    return df.groupby("week", sort=True)[df.columns].apply(write_week_module_file)


if __name__ == "__main__":
    args = docopt(__doc__, version="1.0")
    generate_modules(args["CSV_FILE"])
