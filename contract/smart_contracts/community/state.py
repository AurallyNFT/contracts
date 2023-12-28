import pyteal as P
from beaker.lib.storage import BoxMapping
from smart_contracts.community.boxes import Event, EventTicket, Proposal


class AppState:
    admins = BoxMapping(P.abi.Address, P.abi.String)
    events = BoxMapping(P.abi.String, Event)
    event_tickets = BoxMapping(P.abi.String, EventTicket)
    proposals = BoxMapping(P.abi.String, Proposal)
