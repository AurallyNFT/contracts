from beaker import GlobalStateValue
import pyteal as P
from beaker.lib.storage import BoxMapping
from .boxes import (
    Event,
    EventTicket,
    Proposal,
    AurallyToken,
)


class AppState:
    aurally_nft_owners = BoxMapping(P.abi.Address, AurallyCreative)
    sound_nfts = BoxMapping(P.abi.String, SoundNFT)
    art_nfts = BoxMapping(P.abi.String, ArtNFT)
    art_auctions = BoxMapping(P.abi.String, ArtAuctionItem)
    dao_proposals = BoxMapping(P.abi.String, Proposal)
    registered_asa = BoxMapping(P.abi.String, AurallyToken)
    aurally_admins = BoxMapping(P.abi.Address, P.abi.String)
    events = BoxMapping(P.abi.String, Event)
    event_tickets = BoxMapping(P.abi.String, EventTicket)
    active_proposal = GlobalStateValue(
        stack_type=P.TealType.bytes, default=P.Bytes("None")
    )
