from datetime import datetime, time, timedelta
from typing import Dict, NamedTuple

import aiohttp
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ical.calendar import Calendar
from ical.calendar_stream import IcsCalendarStream
from ical.event import Event
from pydantic import BaseModel, BaseSettings


class Settings(BaseSettings):
    header: dict = {"x-scope": "8a22163c-8662-4535-9050-bc5e1923df48"}
    keyurl: str = "https://web.skola24.se/api/get/timetable/render/key"
    unitsurl: str = (
        "https://web.skola24.se/api/services/skola24/get/timetable/viewer/units"
    )
    scheduleurl: str = "https://web.skola24.se/api/render/timetable"
    selectionurl: str = "https://web.skola24.se/api/get/timetable/selection"
    classesfilter: Dict[str, bool] = {
        "class": True,
        "course": False,
        "group": False,
        "period": False,
        "room": False,
        "student": False,
        "subject": False,
        "teacher": False,
    }


class Domain(BaseModel):
    domain: str


class School(Domain):
    unitguid: str


settings = Settings()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/")
async def get_root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request, "id": 200})


@app.get("/ical/{host}/{unitguid}/{selection}")
async def ical(host: str, unitguid: str, selection: str):
    now = datetime.now()
    weektoget = now - timedelta(days=now.weekday())
    key = await getkey()
    schedule = await getschedule(weektoget, key, host, unitguid, selection)
    return Response(
        content=scheduletoical(weektoget, schedule), media_type="text/calendar"
    )


async def getkey() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            settings.keyurl,
            headers=settings.header,
        ) as resp:
            ret = await resp.json()
            return ret["data"]["key"]


@app.post("/getSchools/")
async def getSchools(domain: Domain):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            settings.unitsurl,
            headers=settings.header,
            json={"getTimetableViewerUnitsRequest": {"hostName": domain.domain}},
        ) as resp:
            schools = await resp.json()
            return schools["data"]["getTimetableViewerUnitsResponse"]["units"]


@app.post("/getClasses/")
async def getClasses(school: School) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            settings.selectionurl,
            headers=settings.header,
            json={
                "hostName": school.domain,
                "unitGuid": school.unitguid,
                "filters": settings.classesfilter,
            },
        ) as response:
            classes = await response.json()
            if classes["error"]:
                raise ValueError("Unknown unitGuid")
            return classes["data"]["classes"]


async def getschedule(
    date: NamedTuple,
    renderkey: str,
    host: str,
    unitguid: str,
    selection: str,
) -> list:
    payload = {
        "renderKey": renderkey,
        "host": host,
        "unitGuid": unitguid,
        "selection": selection,
        "week": datetime.isocalendar(date).week,
        "year": datetime.isocalendar(date).year,
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
            return timetable["data"]["lessonInfo"]


def scheduletoical(weektoget: NamedTuple, schedule: list):
    calendar = Calendar()
    for lesson in schedule:
        weekday = int(lesson["dayOfWeekNumber"]) - 1
        curdate = weektoget + timedelta(days=weekday)
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
