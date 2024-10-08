import beaker as B
import pyteal as P
from smart_contracts.community.boxes import Proposal

from .state import AppState

app = B.Application("Aurally_Community", state=AppState())


@app.external(authorize=B.Authorize.only_creator())
def promote_to_admin(acc: P.abi.Account):
    return P.Seq(
        (is_admin := P.abi.String()).set("True"),
        app.state.admins[acc.address()].set(is_admin),
    )


@app.external(authorize=B.Authorize.only_creator())
def demote_from_admin(acc: P.abi.Account):
    return P.Seq(
        (success := P.abi.Bool()).set(app.state.admins[acc.address()].delete()),
        P.Assert(success.get()),
    )


@app.external(authorize=B.Authorize.only_creator())
def set_nft_app(app_id: P.abi.Uint64) -> P.Expr:
    return P.Seq(app.state.nft_application.set(app_id.get()))


@app.external(authorize=B.Authorize.only_creator())
def set_aura_token(aura: P.abi.Asset):
    return P.Seq(
        (aura_id := P.abi.Uint64()).set(aura.asset_id()),
        app.state.aura_index.set(aura_id.get()),
    )


@app.external
def create_proposal(
    txn: P.abi.PaymentTransaction,
    title: P.abi.String,
    proposal_key: P.abi.String,
    proposal_detail: P.abi.String,
    end_date: P.abi.Uint64,
    *,
    output: Proposal,
):
    from .subroutines.validators import (ensure_is_admin_or_app_creator,
                                         ensure_zero_payment)

    return P.Seq(
        (proposal_creator := P.abi.Address()).set(txn.get().sender()),
        P.Assert(
            app.state.aura_index.exists(),
            comment="Proposals can't be created until aura token is set",
        ),
        ensure_is_admin_or_app_creator(proposal_creator),
        ensure_zero_payment(txn),
        P.Assert(
            P.Not(app.state.proposals[proposal_key.get()].exists()),
            comment="Proposal with this key already exists",
        ),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_total: P.Int(1000000000000),
                P.TxnField.config_asset_name: title.get(),
                P.TxnField.config_asset_manager: P.Global.current_application_address(),
                P.TxnField.config_asset_reserve: P.Global.current_application_address(),
                P.TxnField.config_asset_freeze: P.Global.current_application_address(),
                P.TxnField.config_asset_clawback: P.Global.current_application_address(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (yes_votes := P.abi.Uint64()).set(0),
        (no_votes := P.abi.Uint64()).set(0),
        (ended := P.abi.Bool()).set(False),
        (proposal := Proposal()).set(
            proposal_key,
            asset_id,
            title,
            proposal_detail,
            yes_votes,
            no_votes,
            end_date,
            ended,
        ),
        app.state.proposals[proposal_key.get()].set(proposal),
        output.decode(app.state.proposals[proposal_key.get()].get()),
    )


@app.external
def vote_on_proposal(
    txn: P.abi.PaymentTransaction,
    voter: P.abi.Account,
    vote_for: P.abi.Bool,
    aura: P.abi.Asset,
    proposal_asset: P.abi.Asset,
    proposal_key: P.abi.String,
    *,
    output: Proposal,
):
    from .subroutines.validators import (ensure_proposal_exists,
                                         ensure_zero_payment)

    return P.Seq(
        P.Assert(
            app.state.aura_index.exists(),
            comment="Voting can commence until aura token is set",
        ),
        ensure_zero_payment(txn),
        ensure_proposal_exists(proposal_key),
        P.Assert(aura.asset_id() == app.state.aura_index.get()),
        (proposal := Proposal()).decode(app.state.proposals[proposal_key.get()].get()),
        (key := P.abi.String()).set(proposal.key),
        (asset_id := P.abi.Uint64()).set(proposal.asset_id),
        (title := P.abi.String()).set(proposal.title),
        (details := P.abi.String()).set(proposal.details),
        (yes_votes := P.abi.Uint64()).set(proposal.yes_votes),
        (no_votes := P.abi.Uint64()).set(proposal.no_votes),
        (end_date := P.abi.Uint64()).set(proposal.end_date),
        (ended := P.abi.Bool()).set(proposal.ended),
        P.Assert(
            voter.address() == txn.get().sender(),
            comment="The voter must be the one sending the transaction",
        ),
        (aura_balance := P.AssetHolding.balance(txn.get().sender(), aura.asset_id())),
        P.Assert(P.Not(ended.get()), comment="Voting has ended"),
        P.Assert(
            P.Not(end_date.get() < P.Global.latest_timestamp()),
            comment="Voting has ended",
        ),
        P.Assert(
            proposal_asset.asset_id() == asset_id.get(),
            comment="The proposal asset must match the proposal",
        ),
        P.Assert(
            aura_balance.value() >= P.Int(1), comment="Must have at least 1 aura token"
        ),
        (
            proposal_asset_balance := P.AssetHolding.balance(
                txn.get().sender(), proposal_asset.asset_id()
            )
        ),
        P.Assert(
            P.Not(proposal_asset_balance.hasValue()),
            comment="You've already voted on this proposal",
        ),
        P.If(
            vote_for.get(),
            yes_votes.set(yes_votes.get() + P.Int(1)),
            no_votes.set(no_votes.get() + P.Int(1)),
        ),
        proposal.set(
            key, asset_id, title, details, yes_votes, no_votes, end_date, ended
        ),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: proposal_asset.asset_id(),
                P.TxnField.asset_amount: P.Int(1),
                P.TxnField.asset_receiver: txn.get().sender(),
            }
        ),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetFreeze,
                P.TxnField.freeze_asset: proposal_asset.asset_id(),
                P.TxnField.freeze_asset_account: txn.get().sender(),
                P.TxnField.freeze_asset_frozen: P.Int(1),
            }
        ),
        app.state.proposals[proposal_key.get()].set(proposal),
        output.decode(app.state.proposals[proposal_key.get()].get()),
    )


@app.external
def close_proposal(
    txn: P.abi.PaymentTransaction, proposal_key: P.abi.String, *, output: Proposal
):
    from .subroutines.validators import (ensure_is_admin_or_app_creator,
                                         ensure_proposal_exists,
                                         ensure_zero_payment)

    return P.Seq(
        ensure_zero_payment(txn),
        (proposal_creator := P.abi.Address()).set(txn.get().sender()),
        ensure_is_admin_or_app_creator(proposal_creator),
        ensure_proposal_exists(proposal_key),
        (proposal := Proposal()).decode(app.state.proposals[proposal_key.get()].get()),
        (key := P.abi.String()).set(proposal.key),
        (asset_id := P.abi.Uint64()).set(proposal.asset_id),
        (title := P.abi.String()).set(proposal.title),
        (details := P.abi.String()).set(proposal.details),
        (yes_votes := P.abi.Uint64()).set(proposal.yes_votes),
        (no_votes := P.abi.Uint64()).set(proposal.no_votes),
        (end_date := P.abi.Uint64()).set(proposal.end_date),
        (ended := P.abi.Bool()).set(proposal.ended),
        ended.set(True),
        proposal.set(
            key, asset_id, title, details, yes_votes, no_votes, end_date, ended
        ),
        app.state.proposals[proposal_key.get()].set(proposal),
        output.decode(app.state.proposals[proposal_key.get()].get()),
    )


# @app.external
# def unfreeze_auras(
#     txn: P.abi.PaymentTransaction, aura: P.abi.Asset, acc: P.abi.Account
# ):
#     from .helpers.validators import ensure_auras_frozen_status, ensure_zero_payment
#     from .helpers.transactions import set_aura_frozen
#
#     return P.Seq(
#         ensure_zero_payment(txn),
#         P.Assert(
#             app.state.active_proposal.get() == P.Bytes("None"),
#             comment="Cannot unfreeze while a proposal is still active",
#         ),
#         (auras_frozen_status := P.abi.Bool()).set(False),
#         (address := P.abi.Address()).set(txn.get().sender()),
#         set_aura_frozen(address, auras_frozen_status),
#         ensure_auras_frozen_status(txn, auras_frozen_status),
#     )
#
#
# @app.external
# def create_event(
#     txn: P.abi.PaymentTransaction,
#     key: P.abi.String,
#     name: P.abi.String,
#     start_date: P.abi.Uint64,
#     end_date: P.abi.Uint64,
#     cover_image_ipfs: P.abi.String,
#     ticket_price: P.abi.Uint64,
#     *,
#     output: Event,
# ):
#     from .helpers.validators import ensure_zero_payment
#
#     return P.Seq(
#         ensure_zero_payment(txn),
#         P.Assert(P.Not(app.state.events[key.get()].exists())),
#         P.InnerTxnBuilder.Execute(
#             {
#                 P.TxnField.type_enum: P.TxnType.AssetConfig,
#                 P.TxnField.config_asset_name: name.get(),
#                 P.TxnField.config_asset_total: P.Int(1),
#                 P.TxnField.config_asset_url: cover_image_ipfs.get(),
#                 P.TxnField.config_asset_manager: txn.get().sender(),
#             }
#         ),
#         (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
#         (owner := P.abi.Address()).set(txn.get().sender()),
#         (event := Event()).set(
#             asset_id,
#             key,
#             name,
#             start_date,
#             end_date,
#             cover_image_ipfs,
#             ticket_price,
#             owner,
#         ),
#         app.state.events[key.get()].set(event),
#         output.decode(app.state.events[key.get()].get()),
#     )
#
#
# @app.external
# def purchase_event_ticket(
#     txn: P.abi.PaymentTransaction,
#     event_key: P.abi.String,
#     ticket_key: P.abi.String,
#     event_owner: P.abi.Account,
#     *,
#     output: EventTicket,
# ):
#     from .helpers.transactions import pay_95_percent
#     from .helpers.validators import ensure_event_exists
#
#     return P.Seq(
#         P.Assert(
#             P.Not(app.state.event_tickets[ticket_key.get()].exists()),
#             comment="A ticket with this key already exists",
#         ),
#         ensure_event_exists(event_key),
#         (event := Event()).decode(app.state.events[event_key.get()].get()),
#         (event_owner_address := P.abi.Address()).set(event.owner),
#         (ticket_price := P.abi.Uint64()).set(event.ticket_price),
#         (event_name := P.abi.String()).set(event.name),
#         (event_image_url := P.abi.String()).set(event.cover_image_ipfs),
#         pay_95_percent(txn, ticket_price, event_owner_address),
#         P.InnerTxnBuilder.Execute(
#             {
#                 P.TxnField.type_enum: P.TxnType.AssetConfig,
#                 P.TxnField.config_asset_name: P.Concat(
#                     event_name.get(), P.Bytes(" Ticket")
#                 ),
#                 P.TxnField.config_asset_total: P.Int(1),
#                 P.TxnField.config_asset_url: event_image_url.get(),
#                 P.TxnField.config_asset_manager: txn.get().sender(),
#             }
#         ),
#         (ticket_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
#         (ticket_buyer := P.abi.Address()).set(txn.get().sender()),
#         (ticket := EventTicket()).set(
#             ticket_id, ticket_key, event_key, ticket_price, ticket_buyer
#         ),
#         app.state.event_tickets[ticket_key.get()].set(ticket),
#         output.decode(app.state.event_tickets[ticket_key.get()].get()),
#     )
