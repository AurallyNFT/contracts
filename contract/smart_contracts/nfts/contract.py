import beaker as B  # noqa: N812
import pyteal as P  # noqa: N812
from smart_contracts.nfts.boxes import (
    ArtAuctionItem,
    ArtNFT,
    AurallyCreative,
    AurallyToken,
    AurallyVals,
    SoundNFT,
)

from .state import AppState

app = B.Application("Aurally_NFT", state=AppState()).apply(
    B.unconditional_create_approval, initialize_global_state=True
)


@app.update(authorize=B.Authorize.only_creator(), bare=True)
def update() -> P.Expr:
    return P.Approve()


@app.delete(authorize=B.Authorize.only_creator(), bare=True)
def delete() -> P.Expr:
    return P.Approve()


@app.external(authorize=B.Authorize.only_creator())
def update_commission_percentage(amt: P.abi.Uint8, *, output: P.abi.Uint8) -> P.Expr:
    return P.Seq(
        app.state.commission_percentage.set(amt.get()),
        P.Assert(
            amt.get() <= P.Int(100),
            comment="The commission_percentage must be less that 100%",
        ),
        output.set(app.state.commission_percentage.get()),
    )


@app.external(authorize=B.Authorize.only_creator())
def withdraw_profits(amt: P.abi.Uint64, to: P.abi.Account) -> P.Expr:
    return P.Seq(
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.Payment,
                P.TxnField.amount: amt.get(),
                P.TxnField.receiver: to.address(),
                P.TxnField.note: P.Bytes("Withdrawal from Aurally NFTs"),
            }
        )
    )


@app.external(authorize=B.Authorize.only_creator())
def update_min_charge_price(price: P.abi.Uint64) -> P.Expr:
    return app.state.min_charge_price.set(price.get())


@app.external(authorize=B.Authorize.only_creator())
def create_aura_tokens(*, output: AurallyToken) -> P.Expr:
    from .subroutines.tokens import bootstrap_token

    return P.Seq(
        (token_key := P.abi.String()).set("aura"),
        (unit_name := P.abi.String()).set("AUR"),
        (url := P.abi.String()).set(
            "https://res.cloudinary.com/dev-media/image/upload/v1703091710/Aurally_A_p1v2ob.png"
        ),
        P.If(
            P.Not(app.state.registered_asa[token_key.get()].exists()),
            P.Seq(
                (total := P.abi.Uint64()).set(app.state.total_aurally_tokens.get()),
                bootstrap_token(token_key, total, unit_name, url),
                P.Assert(app.state.registered_asa[token_key.get()].exists()),
            ),
        ),
        output.decode(app.state.registered_asa[token_key.get()].get()),
    )


@app.external(authorize=B.Authorize.only_creator())
def claim_aura_percentage(
    percent_receiver: P.abi.Account, *, output: AurallyToken
) -> P.Expr:
    return P.Seq(
        (token_key := P.abi.String()).set("aura"),
        (token := AurallyToken()).decode(
            app.state.registered_asa[P.Bytes("aura")].get()
        ),
        (asset_id := P.abi.Uint64()).set(token.asset_id),
        (rewardable := P.abi.Uint64()).set(app.state.rewardable_tokens_supply.get()),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: asset_id.get(),
                P.TxnField.asset_receiver: percent_receiver.address(),
                P.TxnField.asset_amount: app.state.total_aurally_tokens.get()
                - rewardable.get(),
            }
        ),
        (claimed := P.abi.Bool()).set(True),  # noqa: FBT003
        token.set(asset_id, token_key, rewardable, claimed),
        app.state.registered_asa[token_key.get()].set(token),
        output.decode(app.state.registered_asa[token_key.get()].get()),
    )


@app.external
def update_aura_rewards(*, output: AurallyVals) -> P.Expr:
    from .subroutines.utils import calculate_and_update_reward

    return P.Seq(
        calculate_and_update_reward(),
        (r := P.abi.Uint64()).set(app.state.aura_reward.get()),
        (r_base := P.abi.Uint64()).set(app.state.aura_base_reward.get()),
        (d := P.abi.Uint64()).set(app.state.network_difficulty.get()),
        output.set(r_base, r, d),
    )


@app.external
def register_creator(txn: P.abi.Transaction, *, output: AurallyCreative) -> P.Expr:
    from .subroutines.records import create_nft_owner

    return P.Seq(
        P.If(
            P.Not(app.state.aurally_nft_owners[txn.get().sender()].exists()),
            create_nft_owner(txn),
        ),
        output.decode(app.state.aurally_nft_owners[txn.get().sender()].get()),
    )


@app.external
def create_sound_nft(
    txn: P.abi.PaymentTransaction,
    nft_name: P.abi.String,
    asset_key: P.abi.String,
    title: P.abi.String,
    label: P.abi.String,
    artist: P.abi.String,
    release_date: P.abi.Uint64,
    genre: P.abi.String,
    description: P.abi.String,
    price: P.abi.Uint64,
    cover_image_url: P.abi.String,
    supply: P.abi.Uint64,
    aura: P.abi.Asset,
    creator: P.abi.Account,
    *,
    output: SoundNFT,
) -> P.Expr:
    from .subroutines.records import (
        increase_app_nft_transaction_count,
        increment_creator_nft_count,
    )
    from .subroutines.transactions import reward_with_aura_tokens
    from .subroutines.validators import (
        ensure_asset_is_aura,
        ensure_sender_is_registered_creative,
        ensure_zero_payment,
    )

    opup = P.OpUp(P.OpUpMode.OnCall)
    return P.Seq(
        opup.maximize_budget(P.Int(1000)),
        ensure_zero_payment(txn),
        ensure_asset_is_aura(aura),
        ensure_sender_is_registered_creative(txn),
        P.Assert(
            creator.address() == txn.get().sender(),
            comment="The creator must be the same as the transaction sender",
        ),
        P.Assert(
            P.Not(app.state.sound_nfts[asset_key.get()].exists()),
            comment="An asset with this key already exists",
        ),
        (creators_address := P.abi.Address()).set(txn.get().sender()),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: nft_name.get(),
                P.TxnField.config_asset_total: supply.get(),
                P.TxnField.config_asset_url: cover_image_url.get(),
                P.TxnField.config_asset_manager: creators_address.get(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (for_sale := P.abi.Bool()).set(True),  # noqa: FBT003
        (claimed := P.abi.Bool()).set(False),  # noqa: FBT003
        (sound_nft := SoundNFT()).set(
            asset_id,
            asset_key,
            supply,
            title,
            label,
            artist,
            release_date,
            genre,
            description,
            price,
            cover_image_url,
            creators_address,
            for_sale,
            claimed,
        ),
        app.state.sound_nfts[asset_key.get()].set(sound_nft),
        increment_creator_nft_count(creators_address),
        increase_app_nft_transaction_count(),
        reward_with_aura_tokens(creators_address),
        output.decode(app.state.sound_nfts[asset_key.get()].get()),
    )


@app.external
def create_art_nft(
    txn: P.abi.PaymentTransaction,
    asset_key: P.abi.String,
    nft_name: P.abi.String,
    title: P.abi.String,
    name: P.abi.String,
    description: P.abi.String,
    image_url: P.abi.String,
    price: P.abi.Uint64,
    aura: P.abi.Asset,
    creator: P.abi.Account,
    *,
    output: ArtNFT,
) -> P.Expr:
    from .subroutines.records import (
        increase_app_nft_transaction_count,
        increment_creator_nft_count,
    )
    from .subroutines.transactions import reward_with_aura_tokens
    from .subroutines.validators import (
        ensure_asset_is_aura,
        ensure_sender_is_registered_creative,
        ensure_zero_payment,
    )

    opup = P.OpUp(P.OpUpMode.OnCall)
    return P.Seq(
        opup.maximize_budget(P.Int(1000)),
        ensure_zero_payment(txn),
        ensure_sender_is_registered_creative(txn),
        ensure_asset_is_aura(aura),
        P.Assert(
            creator.address() == txn.get().sender(),
            comment="The creator must be the same as the transaction sender",
        ),
        P.Assert(
            P.Not(app.state.art_nfts[asset_key.get()].exists()),
            comment="An art NFT with this key already exists",
        ),
        (creators_address := P.abi.Address()).set(txn.get().sender()),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: nft_name.get(),
                P.TxnField.config_asset_total: P.Int(1),
                P.TxnField.config_asset_url: image_url.get(),
                P.TxnField.config_asset_manager: creators_address.get(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (sold_price := P.abi.Uint64()).set(0),
        (for_sale := P.abi.Bool()).set(False),  # noqa: FBT003
        (on_auction := P.abi.Bool()).set(False),  # noqa: FBT003
        (owners_address := P.abi.Address()).set(P.Global.current_application_address()),
        (claimed := P.abi.Bool()).set(False),  # noqa: FBT003
        (art_nft := ArtNFT()).set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            image_url,
            price,
            sold_price,
            creators_address,
            owners_address,
            for_sale,
            on_auction,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
        increment_creator_nft_count(creators_address),
        increase_app_nft_transaction_count(),
        reward_with_aura_tokens(creators_address),
        output.decode(app.state.art_nfts[asset_key.get()].get()),
    )


@app.external
def claim_created_art(
    txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    receiver: P.abi.Account,
    asset: P.abi.Asset,
    *,
    output: ArtNFT,
) -> P.Expr:
    from .subroutines.transactions import transfer_asset_from_contract
    from .subroutines.validators import ensure_art_nft_exists

    return P.Seq(
        ensure_art_nft_exists(asset_key),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (asset_key := P.abi.String()).set(art_nft.asset_key),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (description := P.abi.String()).set(art_nft.description),
        (ipfs_location := P.abi.String()).set(art_nft.image_url),
        (price := P.abi.Uint64()).set(art_nft.price),
        (sold_price := P.abi.Uint64()).set(art_nft.sold_price),
        (creator := P.abi.Address()).set(art_nft.creator),
        (owner := P.abi.Address()).set(art_nft.owner),
        (for_sale := P.abi.Bool()).set(art_nft.for_sale),
        (on_auction := P.abi.Bool()).set(art_nft.on_auction),
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        P.Assert(P.Not(claimed.get()), comment="This art nft has already been claimed"),
        P.Assert(
            receiver.address() == creator.get(),
            comment="The receiver must be the creator of the nft",
        ),
        P.Assert(
            creator.get() == txn.get().sender(),
            comment="This address is not the nft creator",
        ),
        P.Assert(
            asset.asset_id() == asset_id.get(),
            comment="The asset must have the same asset_id as the nft",
        ),
        (amt := P.abi.Uint64()).set(1),
        transfer_asset_from_contract(asset_id, amt, creator),
        owner.set(txn.get().sender()),
        claimed.set(True),  # noqa: FBT003
        art_nft.set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            ipfs_location,
            price,
            sold_price,
            creator,
            owner,
            for_sale,
            on_auction,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
        output.decode(app.state.art_nfts[asset_key.get()].get()),
    )


@app.external
def create_art_auction(
    txn: P.abi.PaymentTransaction,
    auction_key: P.abi.String,
    asset_key: P.abi.String,
    min_bid: P.abi.Uint64,
    starts_at: P.abi.Uint64,
    ends_at: P.abi.Uint64,
    description: P.abi.String,
    *,
    output: ArtAuctionItem,
) -> P.Expr:
    from .subroutines.records import new_art_auction
    from .subroutines.validators import ensure_can_market_art, ensure_zero_payment

    return P.Seq(
        P.Assert(
            P.Not(app.state.art_auctions[auction_key.get()].exists()),
            comment="An auction with this key already exists",
        ),
        ensure_zero_payment(txn),
        P.Assert(
            starts_at.get() < ends_at.get(),
            comment="End date must be greater that start date",
        ),
        ensure_can_market_art(asset_key),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (nft_description := P.abi.String()).set(art_nft.description),
        (image_url := P.abi.String()).set(art_nft.image_url),
        (price := P.abi.Uint64()).set(art_nft.price),
        (sold_price := P.abi.Uint64()).set(art_nft.sold_price),
        (creator := P.abi.Address()).set(art_nft.creator),
        (owner := P.abi.Address()).set(art_nft.owner),
        (for_sale := P.abi.Bool()).set(art_nft.for_sale),
        (on_auction := P.abi.Bool()).set(True),  # noqa: FBT003
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        (nft_name := P.abi.String()).set(art_nft.name),
        art_nft.set(
            asset_id,
            asset_key,
            title,
            name,
            nft_description,
            image_url,
            price,
            sold_price,
            creator,
            owner,
            for_sale,
            on_auction,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
        P.Assert(
            owner.get() == txn.get().sender(),
            comment="Only the owner of this NFT can auction it",
        ),
        new_art_auction(
            txn,
            auction_key,
            asset_key,
            nft_name,
            description,
            min_bid,
            starts_at,
            ends_at,
        ),
        output.decode(app.state.art_auctions[auction_key.get()].get()),
    )


@app.external
def bid_on_art_auction(
    auction_key: P.abi.String,
    txn: P.abi.PaymentTransaction,
    current_highest_bidder: P.abi.Account,
    optin_txn: P.abi.AssetTransferTransaction,
    aura_optin_txn: P.abi.AssetTransferTransaction,
    *,
    output: ArtAuctionItem,
) -> P.Expr:
    from .subroutines.records import record_auction_bid
    from .subroutines.transactions import refund_last_bidder
    from .subroutines.validators import ensure_art_auction_exists

    return P.Seq(
        ensure_art_auction_exists(auction_key),
        P.Assert(txn.get().receiver() == P.Global.current_application_address()),
        (auction := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (auction_name := P.abi.String()).set(auction.item_name),
        (highest_bid := P.abi.Uint64()).set(auction.highest_bid),
        (highest_bidder := P.abi.Address()).set(auction.highest_bidder),
        (min_bid := P.abi.Uint64()).set(auction.min_bid),
        (item_asset_key := P.abi.String()).set(auction.item_asset_key),
        (auction_item := ArtNFT()).decode(
            app.state.art_nfts[item_asset_key.get()].get()
        ),
        (auction_item_id := P.abi.Uint64()).set(auction_item.asset_id),
        (aura := AurallyToken()).decode(
            app.state.registered_asa[P.Bytes("aura")].get()
        ),
        (aura_id := P.abi.Uint64()).set(aura.asset_id),
        P.Assert(
            optin_txn.get().xfer_asset() == auction_item_id.get(),
            comment="Account must opt it to the asset bid on it",
        ),
        P.Assert(
            aura_optin_txn.get().xfer_asset() == aura_id.get(),
            comment="Account mus opt in to aura to bid on asset",
        ),
        P.Assert(
            current_highest_bidder.address() == highest_bidder.get(),
            comment="The current_highest_bidder passed is not the highest_bidder",
        ),
        P.If(
            highest_bid.get() == P.Int(0),
            P.Assert(
                txn.get().amount() > min_bid.get(),
                comment="Bid amount has to be greater than the minimum bid",
            ),
            P.Assert(
                txn.get().amount() > highest_bid.get(),
                comment="Bid amount must be greater that the highest_bid",
            ),
        ),
        P.If(
            P.Not(highest_bidder.get() == P.Global.current_application_address()),
            P.Seq(
                (note := P.abi.String()).set(
                    P.Concat(P.Bytes("Refund for your bid on: "), auction_name.get())
                ),
                refund_last_bidder(current_highest_bidder, highest_bid, note),
            ),
        ),
        record_auction_bid(txn, auction_key),
        output.decode(app.state.art_auctions[auction_key.get()].get()),
    )


@app.external
def complete_art_auction(
    txn: P.abi.AssetTransferTransaction,
    aura: P.abi.Asset,
    auction_key: P.abi.String,
    auctioneer_account: P.abi.Account,
    highest_bidder_account: P.abi.Account,
    *,
    output: ArtNFT,
) -> P.Expr:
    from .subroutines.records import increase_app_nft_transaction_count
    from .subroutines.transactions import (
        pay_price_minus_commission,
        reward_with_aura_tokens,
    )
    from .subroutines.validators import ensure_art_auction_exists

    return P.Seq(
        ensure_art_auction_exists(auction_key),
        (auction_item := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (item_asset_key := P.abi.String()).set(auction_item.item_asset_key),
        (item_name := P.abi.String()).set(auction_item.item_name),
        (auctioneer := P.abi.Address()).set(auction_item.auctioneer),
        (highest_bid := P.abi.Uint64()).set(auction_item.highest_bid),
        (highest_bidder := P.abi.Address()).set(auction_item.highest_bidder),
        # Get the art_nft
        (art_nft := ArtNFT()).decode(app.state.art_nfts[item_asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (asset_key := P.abi.String()).set(art_nft.asset_key),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (description := P.abi.String()).set(art_nft.description),
        (image_url := P.abi.String()).set(art_nft.image_url),
        (price := P.abi.Uint64()).set(art_nft.price),
        (sold_price := P.abi.Uint64()).set(art_nft.sold_price),
        (creator := P.abi.Address()).set(art_nft.creator),
        (owner := P.abi.Address()).set(highest_bidder),  # update the owner
        (for_sale := P.abi.Bool()).set(False),  # noqa: FBT003
        (on_auction := P.abi.Bool()).set(False),  # noqa: FBT003
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        (aura_token := AurallyToken()).decode(
            app.state.registered_asa[P.Bytes("aura")].get()
        ),
        (aura_id := P.abi.Uint64()).set(aura_token.asset_id),
        P.Assert(auctioneer_account.address() == auctioneer.get()),
        P.Assert(
            highest_bidder_account.address() == highest_bidder.get(),
            comment="The passed highest_bidder_account must have the same address as the address of the highest_bidder",  # noqa: E501
        ),
        P.Assert(
            aura.asset_id() == aura_id.get(), comment="The passed asset must be aura"
        ),
        P.Assert(
            txn.get().xfer_asset() == asset_id.get(),
            comment="The asset transferred must be the auctioned asset",
        ),
        P.Assert(
            auctioneer.get() == txn.get().sender(),
            comment="Only the auctioneer is allowed to complete an auction",
        ),
        P.Assert(
            txn.get().asset_receiver() == highest_bidder.get(),
            comment="The asset should be sent to the highest_bidder",
        ),
        art_nft.set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            image_url,
            price,
            sold_price,
            creator,
            owner,
            for_sale,
            on_auction,
            claimed,
        ),
        app.state.art_nfts[item_asset_key.get()].set(art_nft),
        (note := P.abi.String()).set(
            P.Concat(
                P.Bytes("Payment for your completed auction on: "), item_name.get()
            )
        ),
        pay_price_minus_commission(highest_bid, auctioneer, note),
        P.If(highest_bid.get() > P.Int(0), increase_app_nft_transaction_count()),
        reward_with_aura_tokens(highest_bidder),
        output.decode(app.state.art_nfts[item_asset_key.get()].get()),
    )


@app.external
def place_art_on_sale(
    txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    sale_price: P.abi.Uint64,
    *,
    output: ArtNFT,
) -> P.Expr:
    from .subroutines.validators import (
        ensure_asset_receiver_is_application,
        ensure_can_market_art,
    )

    return P.Seq(
        ensure_asset_receiver_is_application(txn),
        ensure_can_market_art(asset_key),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (asset_key := P.abi.String()).set(art_nft.asset_key),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (description := P.abi.String()).set(art_nft.description),
        (image_url := P.abi.String()).set(art_nft.image_url),
        (sold_price := P.abi.Uint64()).set(art_nft.sold_price),
        (creator := P.abi.Address()).set(art_nft.creator),
        (owner := P.abi.Address()).set(art_nft.owner),
        (for_sale := P.abi.Bool()).set(True),  # noqa: FBT003
        (on_auction := P.abi.Bool()).set(art_nft.on_auction),
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        art_nft.set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            image_url,
            sale_price,
            sold_price,
            creator,
            owner,
            for_sale,
            on_auction,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
        P.Assert(
            txn.get().xfer_asset() == asset_id.get(),
            comment="The asset being transferred is not the same as the specified asset_key",  # noqa: E501
        ),
        output.decode(app.state.art_nfts[asset_key.get()].get()),
    )


@app.external
def purchase_nft(
    txn: P.abi.PaymentTransaction,
    optin_txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    asset_type: P.abi.String,
    buyer: P.abi.Account,
    asset: P.abi.Asset,
    aura: P.abi.Asset,
    seller_account: P.abi.Account,
    aura_optin_txn: P.abi.AssetTransferTransaction,
) -> P.Expr:
    from .subroutines.records import increase_app_nft_transaction_count
    from .subroutines.transactions import (
        pay_price_minus_commission,
        reward_with_aura_tokens,
    )
    from .subroutines.validators import (
        ensure_art_nft_exists,
        ensure_asset_is_aura,
        ensure_sound_nft_exists,
        ensure_txn_is_aura_optin,
        ensure_valid_nft_type,
    )

    asset_id = P.abi.Uint64()
    price = P.abi.Uint64()
    seller = P.abi.Address()
    nft_name = P.abi.String()
    opup = P.OpUp(P.OpUpMode.OnCall)
    return P.Seq(
        opup.maximize_budget(P.Int(1000)),
        ensure_valid_nft_type(asset_type),
        ensure_asset_is_aura(aura),
        ensure_txn_is_aura_optin(aura_optin_txn),
        P.If(
            asset_type.get() == P.Bytes("sound"),
            P.Seq(
                ensure_sound_nft_exists(asset_key),
                (nft := SoundNFT()).decode(app.state.sound_nfts[asset_key.get()].get()),
                asset_id.set(nft.asset_id),
                price.set(nft.price),
                seller.set(nft.creator),
                (supply := P.abi.Uint64()).set(nft.supply),
                nft_name.set(nft.title),
                (label := P.abi.String()).set(nft.label),
                (artist := P.abi.String()).set(nft.artist),
                (release_date := P.abi.Uint64()).set(nft.release_date),
                (genre := P.abi.String()).set(nft.genre),
                (description := P.abi.String()).set(nft.description),
                (cover_image_url := P.abi.String()).set(nft.cover_image_url),
                (creator := P.abi.Address()).set(nft.creator),
                (for_sale := P.abi.Bool()).set(nft.for_sale),
                (claimed := P.abi.Bool()).set(nft.claimed),
                P.Assert(supply.get() > P.Int(0), comment="The supply is exhausted"),
                supply.set(supply.get() - P.Int(1)),
                nft.set(
                    asset_id,
                    asset_key,
                    supply,
                    nft_name,
                    label,
                    artist,
                    release_date,
                    genre,
                    description,
                    price,
                    cover_image_url,
                    creator,
                    for_sale,
                    claimed,
                ),
                app.state.sound_nfts[asset_key.get()].set(nft),
            ),
            P.Seq(
                ensure_art_nft_exists(asset_key),
                (nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
                (title := P.abi.String()).set(nft.title),
                nft_name.set(nft.name),
                (description := P.abi.String()).set(nft.description),
                (image_url := P.abi.String()).set(nft.image_url),
                (sold_price := P.abi.Uint64()).set(nft.sold_price),
                (creator := P.abi.Address()).set(nft.creator),
                (for_sale := P.abi.Bool()).set(False),  # noqa: FBT003
                (on_auction := P.abi.Bool()).set(False),  # noqa: FBT003
                (claimed := P.abi.Bool()).set(nft.claimed),
                asset_id.set(nft.asset_id),
                price.set(nft.price),
                seller.set(nft.owner),
                nft.set(
                    asset_id,
                    asset_key,
                    title,
                    nft_name,
                    description,
                    image_url,
                    price,
                    sold_price,
                    creator,
                    seller,
                    for_sale,
                    on_auction,
                    claimed,
                ),
                app.state.art_nfts[asset_key.get()].set(nft),
            ),
        ),
        P.Assert(seller_account.address() == seller.get()),
        P.Assert(
            txn.get().amount() == price.get(),
            comment="The payment amount must be equat to the sale price",
        ),
        P.Assert(
            txn.get().receiver() == P.Global.current_application_address(),
            comment="The payment receiver must be the current_application_address",
        ),
        P.Assert(
            buyer.address() == txn.get().sender(),
            comment="The buyer must be the same as the person make the transaction",
        ),
        (buyers_address := P.abi.Address()).set(txn.get().sender()),
        P.Assert(
            optin_txn.get().xfer_asset() == asset_id.get(),
            comment="The opt-in_txn should be for the asset being purchased",
        ),
        P.Assert(
            asset.asset_id() == asset_id.get(),
            comment="The passed asset must be the same a the asset being purchased",
        ),
        (amt := P.abi.Uint64()).set(1),
        (note := P.abi.String()).set(
            P.Concat(P.Bytes("Payment for purchase of your asset: "), nft_name.get())
        ),
        pay_price_minus_commission(price, seller, note),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: asset_id.get(),
                P.TxnField.asset_receiver: txn.get().sender(),
                P.TxnField.note: P.Bytes("You asset purchase"),
                P.TxnField.asset_amount: amt.get(),
            }
        ),
        P.If(price.get() > P.Int(0), increase_app_nft_transaction_count()),
        reward_with_aura_tokens(buyers_address),
    )
