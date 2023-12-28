import pyteal as P

from smart_contracts.nfts.boxes import AurallyToken


@P.Subroutine(P.TealType.none)
def reward_with_aura_tokens(receiver: P.abi.Address):
    from smart_contracts.nfts.contract import app
    from .validators import ensure_auras_exist

    return P.Seq(
        ensure_auras_exist(),
        (aura_asset_key := P.abi.String()).set("aura"),
        (aura_asset := AurallyToken()).decode(
            app.state.registered_asa[aura_asset_key.get()].get()
        ),
        (aura_asset_id := P.abi.Uint64()).set(aura_asset.asset_id),
        (aura_asset_total := P.abi.Uint64()).set(aura_asset.asset_total),
        (claimed := P.abi.Bool()).set(aura_asset.claimed),
        (note := P.abi.String()).set(""),
        P.If(
            aura_asset_total.get() > P.Int(0),
            note.set("Transaction Reward"),
            note.set("No more transaction rewards"),
        ),
        # Perform Asset Transfer
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: aura_asset_id.get(),
                P.TxnField.asset_receiver: receiver.get(),
                P.TxnField.asset_amount: app.state.aura_reward.get(),
                P.TxnField.note: note.get()
            }
        ),
        # Update Asset Total
        aura_asset_total.set(aura_asset_total.get() - P.Int(1)),
        aura_asset.set(aura_asset_id, aura_asset_key, aura_asset_total, claimed),
        app.state.registered_asa[aura_asset_key.get()].set(aura_asset),
    )


@P.Subroutine(P.TealType.none)
def transfer_asset_from_contract(
    asset_id: P.abi.Uint64, amt: P.abi.Uint64, to: P.abi.Address
):
    return P.Seq(
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: asset_id.get(),
                P.TxnField.asset_amount: amt.get(),
                P.TxnField.asset_receiver: to.get(),
            }
        )
    )


@P.Subroutine(P.TealType.none)
def refund_last_bidder(account: P.abi.Account, amt: P.abi.Uint64, note: P.abi.String):
    return P.Seq(
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.Payment,
                P.TxnField.amount: amt.get(),
                P.TxnField.receiver: account.address(),
                P.TxnField.note: note.get(),
            }
        )
    )
