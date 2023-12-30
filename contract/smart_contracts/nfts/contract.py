import beaker as B
import pyteal as P

from smart_contracts.nfts.boxes import (
    ArtAuctionItem,
    ArtNFT,
    AurallyCreative,
    AurallyToken,
    FixedAssetSale,
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
def create_aura_tokens(*, output: AurallyToken):
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
def claim_aura_percentage(percent_reciever: P.abi.Account, *, output: AurallyToken):
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
                P.TxnField.asset_receiver: percent_reciever.address(),
                P.TxnField.asset_amount: app.state.total_aurally_tokens.get()
                - rewardable.get(),
            }
        ),
        (claimed := P.abi.Bool()).set(True),
        token.set(asset_id, token_key, rewardable, claimed),
        app.state.registered_asa[token_key.get()].set(token),
        output.decode(app.state.registered_asa[token_key.get()].get()),
    )


@app.external(authorize=B.Authorize.only_creator())
def update_scalling_constant(constant: P.abi.Uint64, *, output: P.abi.Uint64):
    return P.Seq(
        app.state.scaling_constant.set(constant.get()),
        output.set(app.state.scaling_constant.get()),
    )


@app.external(authorize=B.Authorize.only_creator())
def update_epoch_target(target: P.abi.Uint64, *, output: P.abi.Uint64):
    return P.Seq(
        app.state.epoch_target_transaction.set(target.get()),
        output.set(app.state.epoch_target_transaction.get()),
    )


@app.external
def update_aura_rewards(*, output: P.abi.Uint64):
    from .subroutines.utils import calculate_and_update_reward

    return P.Seq(
        P.If(
            app.state.total_nft_transactions.get() == P.Int(0),
            app.state.aura_reward.set(P.Int(1)),
            calculate_and_update_reward(),
        ),
        output.set(app.state.aura_reward.get()),
    )


@app.external
def register_creator(
    txn: P.abi.Transaction,
    fullname: P.abi.String,
    username: P.abi.String,
    *,
    output: AurallyCreative,
):
    from .subroutines.records import create_nft_owner

    return P.Seq(
        P.If(
            P.Not(app.state.aurally_nft_owners[txn.get().sender()].exists()),
            create_nft_owner(txn, fullname, username),
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
    cover_image_ipfs: P.abi.String,
    audio_sample_ipfs: P.abi.String,
    full_track_ipfs: P.abi.String,
    supply: P.abi.Uint64,
    aura: P.abi.Asset,
    creator: P.abi.Account,
    *,
    output: SoundNFT,
):
    from .subroutines.records import (
        increment_creator_nft_count,
        increase_app_nft_transaction_count,
    )
    from .subroutines.transactions import reward_with_aura_tokens
    from .subroutines.validators import (
        ensure_registered_creative,
        ensure_zero_payment,
        ensure_asset_is_aura,
    )

    opup = P.OpUp(P.OpUpMode.OnCall)
    return P.Seq(
        ensure_zero_payment(txn),
        ensure_asset_is_aura(aura),
        opup.maximize_budget(P.Int(1000)),
        (creative_type := P.abi.String()).set("music"),
        ensure_registered_creative(txn, creative_type),
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
                P.TxnField.config_asset_url: cover_image_ipfs.get(),
                P.TxnField.config_asset_manager: creators_address.get(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (for_sale := P.abi.Bool()).set(True),
        (claimed := P.abi.Bool()).set(False),
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
            cover_image_ipfs,
            audio_sample_ipfs,
            full_track_ipfs,
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
def claim_created_sound(
    txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    reciever: P.abi.Account,
    asset: P.abi.Asset,
    *,
    output: SoundNFT,
):
    from .subroutines.validators import ensure_sound_nft_exists
    from .subroutines.transactions import transfer_asset_from_contract

    return P.Seq(
        ensure_sound_nft_exists(asset_key),
        (sound_nft := SoundNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(sound_nft.asset_id),
        (asset_key := P.abi.String()).set(sound_nft.asset_key),
        (supply := P.abi.Uint64()).set(sound_nft.supply),
        (title := P.abi.String()).set(sound_nft.title),
        (label := P.abi.String()).set(sound_nft.label),
        (artist := P.abi.String()).set(sound_nft.artist),
        (release_date := P.abi.Uint64()).set(sound_nft.release_date),
        (genre := P.abi.String()).set(sound_nft.genre),
        (description := P.abi.String()).set(sound_nft.description),
        (price := P.abi.Uint64()).set(sound_nft.price),
        (cover_image_ipfs := P.abi.String()).set(sound_nft.cover_image_url),
        (audio_sample_ipfs := P.abi.String()).set(sound_nft.audio_sample_url),
        (full_track_ipfs := P.abi.String()).set(sound_nft.full_track_url),
        (creator := P.abi.Address()).set(sound_nft.creator),
        (for_sale := P.abi.Bool()).set(sound_nft.for_sale),
        (claimed := P.abi.Bool()).set(sound_nft.claimed),
        P.Assert(P.Not(claimed.get()), comment="This art nft has already been claimed"),
        P.Assert(
            creator.get() == txn.get().sender(),
            comment="This address is not the nft creator",
        ),
        P.Assert(
            reciever.address() == creator.get(),
            comment="The reciever must be the creator of the nft",
        ),
        P.Assert(
            asset.asset_id() == asset_id.get(),
            comment="The asset must have the same asset_id as the nft",
        ),
        transfer_asset_from_contract(asset_id, supply, creator),
        claimed.set(True),
        sound_nft.set(
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
            cover_image_ipfs,
            audio_sample_ipfs,
            full_track_ipfs,
            creator,
            for_sale,
            claimed,
        ),
        app.state.sound_nfts[asset_key.get()].set(sound_nft),
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
    ipfs_location: P.abi.String,
    price: P.abi.Uint64,
    aura: P.abi.Asset,
    creator: P.abi.Account,
    *,
    output: ArtNFT,
):
    from .subroutines.validators import (
        ensure_zero_payment,
        ensure_registered_creative,
        ensure_asset_is_aura,
    )
    from .subroutines.transactions import reward_with_aura_tokens
    from .subroutines.records import (
        increment_creator_nft_count,
        increase_app_nft_transaction_count,
    )

    opup = P.OpUp(P.OpUpMode.OnCall)
    return P.Seq(
        opup.maximize_budget(P.Int(1000)),
        ensure_zero_payment(txn),
        ensure_asset_is_aura(aura),
        P.Assert(
            creator.address() == txn.get().sender(),
            comment="The creator must be the same as the transaction sender",
        ),
        P.Assert(
            P.Not(app.state.art_nfts[asset_key.get()].exists()),
            comment="An art NFT with this key already exists",
        ),
        (creative_type := P.abi.String()).set("art"),
        ensure_registered_creative(txn, creative_type),
        (creators_address := P.abi.Address()).set(txn.get().sender()),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: nft_name.get(),
                P.TxnField.config_asset_total: P.Int(1),
                P.TxnField.config_asset_url: ipfs_location.get(),
                P.TxnField.config_asset_manager: creators_address.get(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (sold_price := P.abi.Uint64()).set(0),
        (for_sale := P.abi.Bool()).set(True),
        (owners_address := P.abi.Address()).set(P.Global.current_application_address()),
        (claimed := P.abi.Bool()).set(False),
        (art_nft := ArtNFT()).set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            ipfs_location,
            price,
            sold_price,
            creators_address,
            owners_address,
            for_sale,
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
    reciever: P.abi.Account,
    asset: P.abi.Asset,
    *,
    output: ArtNFT,
):
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
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        P.Assert(P.Not(claimed.get()), comment="This art nft has already been claimed"),
        P.Assert(
            reciever.address() == creator.get(),
            comment="The reciever must be the creator of the nft",
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
        claimed.set(True),
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
):
    from .subroutines.validators import ensure_zero_payment
    from .subroutines.records import new_art_auction

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
        P.Assert(
            app.state.art_nfts[asset_key.get()].exists(),
            comment="Art NFT with this key was not found",
        ),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (art_nft_owner := P.abi.Address()).set(art_nft.owner),
        (nft_name := P.abi.String()).set(art_nft.name),
        P.Assert(
            art_nft_owner.get() == txn.get().sender(),
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
):
    from .subroutines.transactions import refund_last_bidder
    from .subroutines.records import record_auction_bid
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
                comment="Bid amount has to be greated than the minimum bid",
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
    highest_bidder_account: P.abi.Account,
    *,
    output: ArtNFT,
):
    from .subroutines.validators import ensure_art_nft_exists, ensure_art_auction_exists
    from .subroutines.records import (
        update_art_nft_owner,
        increase_app_nft_transaction_count,
    )
    from .subroutines.transactions import reward_with_aura_tokens

    return P.Seq(
        ensure_art_auction_exists(auction_key),
        (auction_item := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (item_asset_key := P.abi.String()).set(auction_item.item_asset_key),
        (auctioneer := P.abi.Address()).set(auction_item.auctioneer),
        (highest_bidder := P.abi.Address()).set(auction_item.highest_bidder),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[item_asset_key.get()].get()),
        (art_nft_asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (aura_token := AurallyToken()).decode(
            app.state.registered_asa[P.Bytes("aura")].get()
        ),
        (aura_id := P.abi.Uint64()).set(aura_token.asset_id),
        P.Assert(
            highest_bidder_account.address() == highest_bidder.get(),
            comment="The passed highest_bidder_account must have the same address as the address of the highest_bidder",
        ),
        P.Assert(
            aura.asset_id() == aura_id.get(), comment="The passed asset must be aura"
        ),
        P.Assert(
            txn.get().xfer_asset() == art_nft_asset_id.get(),
            comment="The asset transfered must be the auctioned asset",
        ),
        P.Assert(
            auctioneer.get() == txn.get().sender(),
            comment="Only the auctioneer is allowed to complete an auction",
        ),
        P.Assert(
            txn.get().asset_amount() == P.Int(1),
            comment="You can only transfer one asset at a time",
        ),
        P.Assert(
            txn.get().asset_receiver() == highest_bidder.get(),
            comment="The asset should be sent to the highest_bidder",
        ),
        ensure_art_nft_exists(item_asset_key),
        update_art_nft_owner(item_asset_key, highest_bidder),
        increase_app_nft_transaction_count(),
        reward_with_aura_tokens(highest_bidder),
        output.decode(app.state.art_nfts[item_asset_key.get()].get()),
    )


@app.external
def place_nft_on_sale(
    txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    asset_type: P.abi.String,
    sale_price: P.abi.Uint64,
    sale_key: P.abi.String,
    *,
    output: FixedAssetSale,
):
    from .subroutines.validators import (
        ensure_asset_reciver_is_application,
        ensure_valid_nft_type,
    )
    from .subroutines.records import new_fixed_asset_sale

    asset_id = P.abi.Uint64()

    return P.Seq(
        ensure_valid_nft_type(asset_type),
        P.Assert(
            P.Not(app.state.fixed_asset_sales[sale_key.get()].exists()),
            comment="a fixed_onsale_asset with this key already exists",
        ),
        ensure_asset_reciver_is_application(txn),
        P.If(
            asset_type.get() == P.Bytes("sound"),
            P.Seq(
                (sound_nft := SoundNFT()).decode(
                    app.state.sound_nfts[asset_key.get()].get()
                ),
                asset_id.set(sound_nft.asset_id),
            ),
            P.Seq(
                (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
                asset_id.set(art_nft.asset_id),
            ),
        ),
        P.Assert(
            txn.get().xfer_asset() == asset_id.get(),
            comment="The asset being transfered is not the same as the specified asset_key",
        ),
        new_fixed_asset_sale(txn, sale_key, asset_key, asset_type, sale_price),
        output.decode(app.state.fixed_asset_sales[sale_key.get()].get()),
    )


@app.external
def purchase_nft(
    txn: P.abi.PaymentTransaction,
    optin_txn: P.abi.AssetTransferTransaction,
    sale_key: P.abi.String,
    asset_type: P.abi.String,
    buyer: P.abi.Account,
    asset: P.abi.Asset,
    aura: P.abi.Asset,
    aura_optin_txn: P.abi.AssetTransferTransaction,
    *,
    output: FixedAssetSale
):
    from .subroutines.validators import (
        ensure_fixed_asset_sale_exists,
        ensure_valid_nft_type,
        ensure_sound_nft_exists,
        ensure_art_nft_exists,
    )

    from .subroutines.records import increase_app_nft_transaction_count, update_fixed_asset_sale_supply
    from .subroutines.transactions import reward_with_aura_tokens
    from .subroutines.validators import ensure_asset_is_aura, ensure_txn_is_aura_optin

    asset_id = P.abi.Uint64()
    return P.Seq(
        ensure_fixed_asset_sale_exists(sale_key),
        ensure_valid_nft_type(asset_type),
        ensure_asset_is_aura(aura),
        ensure_txn_is_aura_optin(aura_optin_txn),
        (sale := FixedAssetSale()).decode(
            app.state.fixed_asset_sales[sale_key.get()].get()
        ),
        (sale_asset_key := P.abi.String()).set(sale.asset_key),
        (price := P.abi.Uint64()).set(sale.price),
        (seller := P.abi.Address()).set(sale.seller),
        (asset_key := P.abi.String()).set(sale.asset_key),
        P.Assert(
            txn.get().amount() == price.get(),
            comment="The payment amount must be equat to the sale price",
        ),
        P.Assert(
            txn.get().receiver() == seller.get(),
            comment="The payment reciever must be the sale seller",
        ),
        P.Assert(
            buyer.address() == txn.get().sender(),
            comment="The buyer must be the same as the person make the transaction",
        ),
        P.Assert(
            sale_asset_key.get() == asset_key.get(),
            comment="The asset_key must be the same as the key of the asset to be purchased",
        ),
        P.If(
            asset_type.get() == P.Bytes("sound"),
            P.Seq(
                ensure_sound_nft_exists(asset_key),
                (nft := SoundNFT()).decode(app.state.sound_nfts[asset_key.get()].get()),
                asset_id.set(nft.asset_id),
            ),
            P.Seq(
                ensure_art_nft_exists(asset_key),
                (nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
                asset_id.set(nft.asset_id),
            ),
        ),
        (creators_address := P.abi.Address()).set(txn.get().sender()),
        P.Assert(
            optin_txn.get().xfer_asset() == asset_id.get(),
            comment="The optin_txn should be for the asset being purchased",
        ),
        P.Assert(asset.asset_id() == asset_id.get(), comment="The passed asset must be the same a the asset being purchased"),
        (amt := P.abi.Uint64()).set(1),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: asset_id.get(),
                P.TxnField.asset_receiver: txn.get().sender(),
                P.TxnField.note: P.Bytes("You asset purchase"),
                P.TxnField.asset_amount: amt.get()
            }
        ),
        increase_app_nft_transaction_count(),
        reward_with_aura_tokens(creators_address),
        (action := P.abi.String()).set("subtract"),
        update_fixed_asset_sale_supply(sale_key, amt, action),
        output.decode(app.state.fixed_asset_sales[sale_key.get()].get())
    )


# @app.external
# def transfer_nft(
#     txn: P.abi.PaymentTransaction,
#     to: P.abi.Address,
#     asset_key: P.abi.String,
#     nft_type: P.abi.String,
# ):
#     return P.Seq(
#         P.Assert(txn.get().amount() == P.Int(0)),
#         P.Assert(
#             P.Or(nft_type.get() == P.Bytes("ticket"), nft_type.get() == P.Bytes("art"))
#         ),
#         P.If(
#             nft_type.get() == P.Bytes("art"),
#             P.Seq(
#                 validate_art_nft_owner(txn, asset_key),
#                 update_art_nft_owner(asset_key, to),
#             ),
#         ),
#     )
