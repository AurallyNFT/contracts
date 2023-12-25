import pyteal as P
from smart_contracts.aurally.boxes import (
    ArtNFT,
    AurallyCreative,
    AurallyToken,
    Event,
    SoundNFT,
)
from smart_contracts.aurally.contract import app


@P.Subroutine(P.TealType.none)
def ensure_proposal_exists(proposal_key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.dao_proposals[proposal_key.get()].exists(),
        comment="Proposal with specified key was not found",
    )


@P.Subroutine(P.TealType.none)
def ensure_event_exists(key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.events[key.get()].exists(),
        comment="Event with specified key does not exist",
    )


@P.Subroutine(P.TealType.none)
def ensure_sender_is_event_owner(txn: P.abi.Transaction, key: P.abi.String):
    return P.Seq(
        ensure_event_exists(key),
        (event := Event()).decode(app.state.events[key.get()].get()),
        (owner := P.abi.Address()).set(event.owner),
        P.Assert(
            txn.get().sender() == owner.get(),
            comment="Not event owner: You are not authorised to perform this action",
        ),
    )
