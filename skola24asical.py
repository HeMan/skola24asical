from datetime import datetime, time, timedelta

import aiohttp
from fastapi import FastAPI, Response
from ical.calendar import Calendar
from ical.calendar_stream import IcsCalendarStream
from ical.event import Event
from pydantic import BaseSettings


class Settings(BaseSettings):
    header: dict = {"x-scope": "8a22163c-8662-4535-9050-bc5e1923df48"}
    host: str = "ies.skola24.se"
    unitguid: str = "MDQ5YTFlY2YtZDZkNi1mNTRhLWFjNWMtNGQ1NDhhZTk1ZDdh"
    keyurl: str = "https://web.skola24.se/api/get/timetable/render/key"
    scheduleurl: str = "https://web.skola24.se/api/render/timetable"


settings = Settings()

app = FastAPI()


#
# TODO: argument for selection
# TODO: argument for host
# TODO: argument for unitguid
# TODO: current date


@app.get("/")
async def read_root():
    key = await getkey()
    schedule = await getschedule(key)
    return Response(content=scheduletoical(schedule), media_type="text/calendar")


async def getkey() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            settings.keyurl,
            headers=settings.header,
        ) as resp:
            ret = await resp.json()
            return ret["data"]["key"]


async def getschedule(renderkey: str) -> list:
    payload = {
        "renderKey": renderkey,
        "host": settings.host,
        "unitGuid": settings.unitguid,
        "selection": "MTQ0Mjk4ZDktYzg2My1mODQ4LTkxZmItYmI3YTAxOTQwMDkw",
        "week": 40,
        "year": 2022,
        "width": 1,
        "height": 1,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            settings.scheduleurl,
            headers=settings.header,
            json=payload,
        ) as resp:
            timetable = await resp.json()
            if timetable["validation"]:
                print(timetable)
            return timetable["data"]["lessonInfo"]


def scheduletoical(schedule: list):
    d = "2022-W40"
    dateforfirstday = datetime.strptime(d + "-1", "%G-W%V-%u")
    calendar = Calendar()
    for lesson in schedule:
        weekday = int(lesson["dayOfWeekNumber"]) - 1
        curdate = dateforfirstday + timedelta(days=weekday)
        timestart = time.fromisoformat(lesson["timeStart"])
        timeend = time.fromisoformat(lesson["timeEnd"])
        calendar.events.append(
            Event(
                summary=lesson["texts"][0],
                start=curdate
                + timedelta(hours=timestart.hour, minutes=timestart.minute),
                end=curdate + timedelta(hours=timeend.hour, minutes=timeend.minute),
            )
        )
    return IcsCalendarStream.calendar_to_ics(calendar)
