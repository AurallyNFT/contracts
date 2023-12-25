import beaker as B
import pyteal as P

from smart_contracts.aurally.boxes import (
    Event,
    EventTicket,
    Proposal,
)
from .states import AppState

app = B.Application("Aurally", state=AppState()).apply(
    B.unconditional_create_approval, initialize_global_state=True
)


@app.update(authorize=B.Authorize.only_creator(), bare=True)
def update() -> P.Expr:
    return P.Approve()


@app.delete(authorize=B.Authorize.only_creator(), bare=True)
def delete() -> P.Expr:
    return P.Approve()


@app.external
def promote_to_admin(
    txn: P.abi.PaymentTransaction, acc: P.abi.Account, *, output: P.abi.String
):
    from .helpers.validators import ensure_zero_payment, ensure_sender_is_app_creator

    return P.Seq(
        ensure_zero_payment(txn),
        ensure_sender_is_app_creator(txn),
        P.Assert(P.Not(app.state.aurally_admins[acc.address()].exists())),
        (is_admin := P.abi.String()).set("True"),
        app.state.aurally_admins[acc.address()].set(is_admin),
        output.decode(app.state.aurally_admins[acc.address()].get()),
    )


@app.external
def demote_from_admin(
    txn: P.abi.PaymentTransaction, acc: P.abi.Account, *, output: P.abi.String
):
    from .helpers.validators import ensure_zero_payment, ensure_sender_is_app_creator

    return P.Seq(
        ensure_zero_payment(txn),
        ensure_sender_is_app_creator(txn),
        P.Assert(app.state.aurally_admins[acc.address()].exists()),
        (is_admin := P.abi.String()).set("False"),
        app.state.aurally_admins[acc.address()].set(is_admin),
        output.decode(app.state.aurally_admins[acc.address()].get()),
    )


# Todo: Update SoundNFT owner on creation
# Todo: Update ArtNFT owner on creation


@app.external
def complete_art_auction(
    txn: P.abi.PaymentTransaction, auction_key: P.abi.String, *, output: ArtNFT
):
    from .subroutines import transfer_art_auction_item_to_highest_bidder
    from .helpers.validators import ensure_zero_payment

    return P.Seq(
        ensure_zero_payment(txn),
        P.Assert(
            app.state.art_auctions[auction_key.get()].exists(),
            comment="art auction with the specified key does not exist",
        ),
        (auction_item := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (nft_key := P.abi.String()).set(auction_item.item_id),
        (auctioneer := P.abi.Address()).set(auction_item.auctioneer),
        P.Assert(auctioneer.get() == txn.get().sender()),
        transfer_art_auction_item_to_highest_bidder(auction_key),
        output.decode(app.state.art_nfts[nft_key.get()].get()),
    )


@app.external
def place_nft_on_sale(
    txn: P.abi.PaymentTransaction,
    asset_key: P.abi.String,
    nft_type: P.abi.String,
    asset: P.abi.Asset,
):
    from .subroutines import (
        update_sound_nft_sale,
        update_art_nft_sale,
        validate_sound_nft_owner,
        validate_art_nft_owner,
    )
    from .helpers.validators import ensure_zero_payment

    return P.Seq(
        ensure_zero_payment(txn),
        P.Assert(
            P.Or(nft_type.get() == P.Bytes("art"), nft_type.get() == P.Bytes("sound")),
            comment="nft_type can only be `art` or `sound`",
        ),
        (for_sale := P.abi.Bool()).set(True),
        P.If(
            nft_type.get() == P.Bytes("sound"),
            P.Seq(
                validate_sound_nft_owner(txn, asset_key),
                update_sound_nft_sale(asset_key, for_sale),
            ),
            P.Seq(
                validate_art_nft_owner(txn, asset_key),
                update_art_nft_sale(asset_key, for_sale),
            ),
        ),
    )


@app.external
def purchase_nft(
    txn: P.abi.PaymentTransaction,
    optin_txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    nft_type: P.abi.String,
    seller: P.abi.Account,
    nft_id: P.abi.Asset,
    aura_id: P.abi.Asset,
    aura_optin_txn: P.abi.AssetTransferTransaction,
    buyer: P.abi.Account,
):
    from .subroutines import perform_sound_nft_sale, perform_art_nft_sale

    return P.Seq(
        P.Assert(
            P.Or(nft_type.get() == P.Bytes("sound"), nft_type.get() == P.Bytes("art"))
        ),
        P.If(
            nft_type.get() == P.Bytes("sound"),
            perform_sound_nft_sale(txn, asset_key),
            perform_art_nft_sale(txn, asset_key),
        ),
    )


@app.external
def transfer_nft(
    txn: P.abi.PaymentTransaction,
    to: P.abi.Address,
    asset_key: P.abi.String,
    nft_type: P.abi.String,
):
    from .subroutines import (
        validate_art_nft_owner,
        update_art_nft_owner,
    )

    return P.Seq(
        P.Assert(txn.get().amount() == P.Int(0)),
        P.Assert(
            P.Or(nft_type.get() == P.Bytes("ticket"), nft_type.get() == P.Bytes("art"))
        ),
        P.If(
            nft_type.get() == P.Bytes("art"),
            P.Seq(
                validate_art_nft_owner(txn, asset_key),
                update_art_nft_owner(asset_key, to),
            ),
        ),
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
    from .helpers.validators import (
        ensure_zero_payment,
        ensure_nft_owner_exists_from_txn,
        ensure_is_admin_or_app_creator,
    )

    return P.Seq(
        (proposal_creator := P.abi.Address()).set(txn.get().sender()),
        ensure_is_admin_or_app_creator(proposal_creator),
        ensure_zero_payment(txn),
        ensure_nft_owner_exists_from_txn(txn),
        P.Assert(
            app.state.active_proposal.get() == P.Bytes("None"),
            comment="There's already an active proposal",
        ),
        P.Assert(
            P.Not(app.state.dao_proposals[proposal_key.get()].exists()),
            comment="Proposal with this key already exists",
        ),
        (yes_votes := P.abi.Uint64()).set(0),
        (no_votes := P.abi.Uint64()).set(0),
        (proposal := Proposal()).set(
            proposal_key, title, yes_votes, no_votes, proposal_detail, end_date
        ),
        app.state.dao_proposals[proposal_key.get()].set(proposal),
        app.state.active_proposal.set(proposal_key.get()),
        output.decode(app.state.dao_proposals[proposal_key.get()].get()),
    )


@app.external
def vote_on_proposal(
    txn: P.abi.PaymentTransaction,
    vote_for: P.abi.Bool,
    aura_id: P.abi.Asset,
    voter: P.abi.Account,
    proposal_key: P.abi.String,
    *,
    output: Proposal,
):
    from .helpers.validators import (
        ensure_has_auras,
        ensure_auras_frozen_status,
        ensure_zero_payment,
        ensure_proposal_exists,
        ensure_nft_owner_exists_from_txn,
    )

    from .helpers.transactions import set_aura_frozen

    return P.Seq(
        ensure_nft_owner_exists_from_txn(txn),
        ensure_zero_payment(txn),
        ensure_proposal_exists(proposal_key),
        P.Assert(
            proposal_key.get() == app.state.active_proposal.get(),
            comment="This proposal is currenlty not active",
        ),
        ensure_has_auras(txn),
        (auras_frozen_status := P.abi.Bool()).set(False),
        ensure_auras_frozen_status(txn, auras_frozen_status),
        (proposal := Proposal()).decode(
            app.state.dao_proposals[proposal_key.get()].get()
        ),
        (proposal_id := P.abi.String()).set(proposal.key),
        (proposal_title := P.abi.String()).set(proposal.title),
        (yes_votes := P.abi.Uint64()).set(proposal.yes_votes),
        (no_votes := P.abi.Uint64()).set(proposal.no_votes),
        (details := P.abi.String()).set(proposal.details),
        (proposal_end_date := P.abi.Uint64()).set(proposal.end_date),
        P.If(
            vote_for.get(),
            yes_votes.set(yes_votes.get() + P.Int(1)),
            no_votes.set(no_votes.get() + P.Int(1)),
        ),
        proposal.set(
            proposal_id, proposal_title, yes_votes, no_votes, details, proposal_end_date
        ),
        app.state.dao_proposals[proposal_key.get()].set(proposal),
        auras_frozen_status.set(True),
        (voters_address := P.abi.Address()).set(txn.get().sender()),
        set_aura_frozen(voters_address, auras_frozen_status),
        ensure_auras_frozen_status(txn, auras_frozen_status),
        output.decode(app.state.dao_proposals[proposal_key.get()].get()),
    )


@app.external
def end_proposal_voting(
    txn: P.abi.PaymentTransaction, proposal_key: P.abi.String, *, output: Proposal
):
    from .helpers.validators import (
        ensure_zero_payment,
        ensure_is_admin_or_app_creator,
        ensure_proposal_exists,
    )

    return P.Seq(
        ensure_zero_payment(txn),
        (proposal_creator := P.abi.Address()).set(txn.get().sender()),
        ensure_is_admin_or_app_creator(proposal_creator),
        ensure_proposal_exists(proposal_key),
        P.Assert(app.state.active_proposal.get() == proposal_key.get()),
        app.state.active_proposal.set(P.Bytes("None")),
        output.decode(app.state.dao_proposals[proposal_key.get()].get()),
    )


@app.external
def unfreeze_auras(
    txn: P.abi.PaymentTransaction, aura: P.abi.Asset, acc: P.abi.Account
):
    from .helpers.validators import ensure_auras_frozen_status, ensure_zero_payment
    from .helpers.transactions import set_aura_frozen

    return P.Seq(
        ensure_zero_payment(txn),
        P.Assert(
            app.state.active_proposal.get() == P.Bytes("None"),
            comment="Cannot unfreeze while a proposal is still active",
        ),
        (auras_frozen_status := P.abi.Bool()).set(False),
        (address := P.abi.Address()).set(txn.get().sender()),
        set_aura_frozen(address, auras_frozen_status),
        ensure_auras_frozen_status(txn, auras_frozen_status),
    )


@app.external
def create_event(
    txn: P.abi.PaymentTransaction,
    key: P.abi.String,
    name: P.abi.String,
    start_date: P.abi.Uint64,
    end_date: P.abi.Uint64,
    cover_image_ipfs: P.abi.String,
    ticket_price: P.abi.Uint64,
    *,
    output: Event,
):
    from .helpers.validators import ensure_zero_payment

    return P.Seq(
        ensure_zero_payment(txn),
        P.Assert(P.Not(app.state.events[key.get()].exists())),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: name.get(),
                P.TxnField.config_asset_total: P.Int(1),
                P.TxnField.config_asset_url: cover_image_ipfs.get(),
                P.TxnField.config_asset_manager: txn.get().sender(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (owner := P.abi.Address()).set(txn.get().sender()),
        (event := Event()).set(
            asset_id,
            key,
            name,
            start_date,
            end_date,
            cover_image_ipfs,
            ticket_price,
            owner,
        ),
        app.state.events[key.get()].set(event),
        output.decode(app.state.events[key.get()].get()),
    )


@app.external
def purchase_event_ticket(
    txn: P.abi.PaymentTransaction,
    event_key: P.abi.String,
    ticket_key: P.abi.String,
    event_owner: P.abi.Account,
    *,
    output: EventTicket,
):
    from .helpers.transactions import pay_95_percent
    from .helpers.validators import ensure_event_exists

    return P.Seq(
        P.Assert(
            P.Not(app.state.event_tickets[ticket_key.get()].exists()),
            comment="A ticket with this key already exists",
        ),
        ensure_event_exists(event_key),
        (event := Event()).decode(app.state.events[event_key.get()].get()),
        (event_owner_address := P.abi.Address()).set(event.owner),
        (ticket_price := P.abi.Uint64()).set(event.ticket_price),
        (event_name := P.abi.String()).set(event.name),
        (event_image_url := P.abi.String()).set(event.cover_image_ipfs),
        pay_95_percent(txn, ticket_price, event_owner_address),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: P.Concat(
                    event_name.get(), P.Bytes(" Ticket")
                ),
                P.TxnField.config_asset_total: P.Int(1),
                P.TxnField.config_asset_url: event_image_url.get(),
                P.TxnField.config_asset_manager: txn.get().sender(),
            }
        ),
        (ticket_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (ticket_buyer := P.abi.Address()).set(txn.get().sender()),
        (ticket := EventTicket()).set(
            ticket_id, ticket_key, event_key, ticket_price, ticket_buyer
        ),
        app.state.event_tickets[ticket_key.get()].set(ticket),
        output.decode(app.state.event_tickets[ticket_key.get()].get()),
    )


@app.external
def hello(name: P.abi.String, *, output: P.abi.String) -> P.Expr:
    return output.set(P.Concat(name.get(), P.Bytes(" World")))
