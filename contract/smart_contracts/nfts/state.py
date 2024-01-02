from beaker.state import GlobalStateValue
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

    aura_reward = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    aura_base_reward = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    epoch_nft_transactions = GlobalStateValue(P.TealType.uint64, default=P.Int(0))
    epoch_target_transaction = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    total_nft_transactions = GlobalStateValue(P.TealType.uint64, default=P.Int(0))
    network_difficulty = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    scaling_constant = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    total_aurally_tokens = GlobalStateValue(
        P.TealType.uint64, default=P.Int(100000000), static=True
    )
    rewardable_tokens_supply = GlobalStateValue(
        P.TealType.uint64, default=P.Int(80000000)
    )
