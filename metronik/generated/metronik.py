from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://www.metronik.si/"


@dataclass(kw_only=True)
class RoomDescriptor:
    faculty: None | str = field(
        default=None,
        metadata={
            "name": "Faculty",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        },
    )
    valid_from: XmlDateTime = field(
        metadata={
            "name": "ValidFrom",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        }
    )
    valid_to: XmlDateTime = field(
        metadata={
            "name": "ValidTo",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        }
    )
    room: None | str = field(
        default=None,
        metadata={
            "name": "Room",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        },
    )
    week_day: int = field(
        metadata={
            "name": "WeekDay",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        }
    )


@dataclass(kw_only=True)
class TimeDescriptor:
    occupied: bool = field(
        metadata={
            "name": "Occupied",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        }
    )
    from_value: XmlDateTime = field(
        metadata={
            "name": "From",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        }
    )
    to: XmlDateTime = field(
        metadata={
            "name": "To",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
        }
    )


@dataclass(kw_only=True)
class TimetableTransferResponse:
    class Meta:
        namespace = "http://www.metronik.si/"


@dataclass(kw_only=True)
class ArrayOfTimeDescriptor:
    time_descriptor: list[TimeDescriptor] = field(
        default_factory=list,
        metadata={
            "name": "TimeDescriptor",
            "type": "Element",
            "namespace": "http://www.metronik.si/",
            "nillable": True,
        },
    )


@dataclass(kw_only=True)
class WebServiceSoapTimetableTransferOutput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    body: WebServiceSoapTimetableTransferOutput.Body = field(
        metadata={
            "name": "Body",
            "type": "Element",
        }
    )

    @dataclass(kw_only=True)
    class Body:
        timetable_transfer_response: None | TimetableTransferResponse = field(
            default=None,
            metadata={
                "name": "TimetableTransferResponse",
                "type": "Element",
                "namespace": "http://www.metronik.si/",
            },
        )
        fault: None | WebServiceSoapTimetableTransferOutput.Body.Fault = field(
            default=None,
            metadata={
                "name": "Fault",
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class Fault:
            faultcode: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "",
                }
            )
            faultstring: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "",
                }
            )
            faultactor: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )
            detail: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )


@dataclass(kw_only=True)
class TimetableTransfer:
    class Meta:
        namespace = "http://www.metronik.si/"

    room: None | RoomDescriptor = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    times: None | ArrayOfTimeDescriptor = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass(kw_only=True)
class WebServiceSoapTimetableTransferInput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    body: WebServiceSoapTimetableTransferInput.Body = field(
        metadata={
            "name": "Body",
            "type": "Element",
        }
    )

    @dataclass(kw_only=True)
    class Body:
        timetable_transfer: TimetableTransfer = field(
            metadata={
                "name": "TimetableTransfer",
                "type": "Element",
                "namespace": "http://www.metronik.si/",
            }
        )


class WebServiceSoapTimetableTransfer:
    style = "document"
    location = "http://192.168.190.81/Fri.Webservice/webservice.asmx"
    transport = "http://schemas.xmlsoap.org/soap/http"
    soap_action = "http://www.metronik.si/TimetableTransfer"
    input = WebServiceSoapTimetableTransferInput
    output = WebServiceSoapTimetableTransferOutput
