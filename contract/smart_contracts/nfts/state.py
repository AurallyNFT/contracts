import pyteal as P
from beaker.lib.storage import BoxMapping

from smart_contracts.nfts.boxes import (
    ArtAuctionItem,
    ArtNFT,
    AurallyCreative,
    AurallyToken,
    SoundNFT,
)


class AppState:
    aurally_nft_owners = BoxMapping(P.abi.Address, AurallyCreative)
    sound_nfts = BoxMapping(P.abi.String, SoundNFT)
    art_nfts = BoxMapping(P.abi.String, ArtNFT)
    art_auctions = BoxMapping(P.abi.String, ArtAuctionItem)
    registered_asa = BoxMapping(P.abi.String, AurallyToken)
