import pyteal as P


class AurallyVals(P.abi.NamedTuple):
    reward_base: P.abi.Field[P.abi.Uint64]
    reward: P.abi.Field[P.abi.Uint64]
    difficulty: P.abi.Field[P.abi.Uint64]


class AurallyCreative(P.abi.NamedTuple):
    """
    Represents a registered account
    """

    address: P.abi.Field[P.abi.Address]
    minted: P.abi.Field[P.abi.Uint64]
    d_nft_id: P.abi.Field[P.abi.Uint64]


class SoundNFT(P.abi.NamedTuple):
    asset_id: P.abi.Field[P.abi.Uint64]
    asset_key: P.abi.Field[P.abi.String]
    supply: P.abi.Field[P.abi.Uint64]
    title: P.abi.Field[P.abi.String]
    label: P.abi.Field[P.abi.String]
    artist: P.abi.Field[P.abi.String]
    release_date: P.abi.Field[P.abi.Uint64]  # A UTC timestamp of the release_date
    genre: P.abi.Field[P.abi.String]
    description: P.abi.Field[P.abi.String]
    price: P.abi.Field[P.abi.Uint64]
    cover_image_url: P.abi.Field[P.abi.String]
    audio_sample_id: P.abi.Field[P.abi.String]
    full_track_id: P.abi.Field[P.abi.String]
    creator: P.abi.Field[P.abi.Address]
    for_sale: P.abi.Field[P.abi.Bool]
    claimed: P.abi.Field[P.abi.Bool]


class ArtNFT(P.abi.NamedTuple):
    asset_id: P.abi.Field[P.abi.Uint64]
    asset_key: P.abi.Field[P.abi.String]
    title: P.abi.Field[P.abi.String]
    name: P.abi.Field[P.abi.String]
    description: P.abi.Field[P.abi.String]
    image_url: P.abi.Field[P.abi.String]
    price: P.abi.Field[P.abi.Uint64]
    sold_price: P.abi.Field[P.abi.Uint64]
    creator: P.abi.Field[P.abi.Address]
    owner: P.abi.Field[P.abi.Address]
    for_sale: P.abi.Field[P.abi.Bool]
    on_auction: P.abi.Field[P.abi.Bool]
    claimed: P.abi.Field[P.abi.Bool]


class ArtAuctionItem(P.abi.NamedTuple):
    auction_key: P.abi.Field[P.abi.String]
    auctioneer: P.abi.Field[P.abi.Address]
    item_asset_key: P.abi.Field[P.abi.String]
    item_name: P.abi.Field[P.abi.String]
    min_bid: P.abi.Field[P.abi.Uint64]
    starts_at: P.abi.Field[P.abi.Uint64]
    ends_at: P.abi.Field[P.abi.Uint64]
    description: P.abi.Field[P.abi.String]
    highest_bid: P.abi.Field[P.abi.Uint64]
    highest_bidder: P.abi.Field[P.abi.Address]
    closed: P.abi.Field[P.abi.Bool]


class AurallyToken(P.abi.NamedTuple):
    asset_id: P.abi.Field[P.abi.Uint64]
    asset_key: P.abi.Field[P.abi.String]
    asset_total: P.abi.Field[P.abi.Uint64]
    claimed: P.abi.Field[P.abi.Bool]
