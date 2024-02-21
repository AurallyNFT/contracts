import pyteal as P
from beaker.lib.storage import BoxMapping
from beaker.state import GlobalStateValue
from smart_contracts.community.boxes import Event, EventTicket, Proposal


class AppState:
    admins = BoxMapping(P.abi.Address, P.abi.String)
    events = BoxMapping(P.abi.String, Event)
    event_tickets = BoxMapping(P.abi.String, EventTicket)
    proposals = BoxMapping(P.abi.String, Proposal)
    aura_index = GlobalStateValue(P.TealType.uint64)
    nft_application = GlobalStateValue(P.TealType.uint64)
