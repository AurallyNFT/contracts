import pyteal as P
from beaker.lib.storage import BoxMapping
from beaker.state import GlobalStateValue
from smart_contracts.nfts.boxes import (ArtAuctionItem, ArtNFT,
                                        AurallyCreative, AurallyToken,
                                        SoundNFT)

# Todo: NFT Sales above 1 algos are the only ones that are charged
# Idea: Create an asa for each proposal, when a person votes on a proposal, they get the asa and it's frozen


class AppState:
    aurally_nft_owners = BoxMapping(P.abi.Address, AurallyCreative)
    sound_nfts = BoxMapping(P.abi.String, SoundNFT)
    art_nfts = BoxMapping(P.abi.String, ArtNFT)
    art_auctions = BoxMapping(P.abi.String, ArtAuctionItem)
    registered_asa = BoxMapping(P.abi.String, AurallyToken)
    commission_percentage = GlobalStateValue(P.TealType.uint64, default=P.Int(10))

    epoch_nft_transactions = GlobalStateValue(P.TealType.uint64, default=P.Int(0))
    epoch_target_transaction = GlobalStateValue(
        P.TealType.uint64, default=P.Int(500)
    )  # 365 years
    total_nft_transactions = GlobalStateValue(P.TealType.uint64, default=P.Int(0))
    min_difficulty = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    network_difficulty = GlobalStateValue(P.TealType.uint64, default=P.Int(1))

    total_target_nft_sales = GlobalStateValue(
        P.TealType.uint64, default=P.Int(1600000000)
    )
    total_aurally_tokens = GlobalStateValue(
        P.TealType.uint64, default=P.Int(100000000000000), static=True
    )
    rewardable_tokens_supply = GlobalStateValue(
        P.TealType.uint64, default=P.Int(80000000000000)
    )

    min_aural_reward = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    aura_reward = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
    aura_base_reward = GlobalStateValue(P.TealType.uint64, default=P.Int(1))

    min_charge_price = GlobalStateValue(P.TealType.uint64, default=P.Int(1))
