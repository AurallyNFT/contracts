import pyteal as P


class Proposal(P.abi.NamedTuple):
    key: P.abi.Field[P.abi.String]
    title: P.abi.Field[P.abi.String]
    yes_votes: P.abi.Field[P.abi.Uint64]
    no_votes: P.abi.Field[P.abi.Uint64]
    details: P.abi.Field[P.abi.String]
    end_date: P.abi.Field[P.abi.Uint64]


class Event(P.abi.NamedTuple):
    asset_id: P.abi.Field[P.abi.Uint64]
    key: P.abi.Field[P.abi.String]
    name: P.abi.Field[P.abi.String]
    start_date: P.abi.Field[P.abi.Uint64]
    end_date: P.abi.Field[P.abi.Uint64]
    cover_image_ipfs: P.abi.Field[P.abi.String]
    ticket_price: P.abi.Field[P.abi.Uint64]
    owner: P.abi.Field[P.abi.Address]


class EventTicket(P.abi.NamedTuple):
    asset_id: P.abi.Field[P.abi.Uint64]
    ticket_key: P.abi.Field[P.abi.String]
    event_asset_key: P.abi.Field[P.abi.String]
    purchase_price: P.abi.Field[P.abi.Uint64]
    owner: P.abi.Field[P.abi.Address]
