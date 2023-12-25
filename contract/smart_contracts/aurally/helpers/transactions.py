import pyteal as P

from smart_contracts.aurally.boxes import AurallyToken
from smart_contracts.aurally.contract import app


@P.Subroutine(P.TealType.none)
def set_aura_frozen(address: P.abi.Address, to: P.abi.Bool):
    from .validators import ensure_auras_exist

    return P.Seq(
        ensure_auras_exist(),
        (aura_token := AurallyToken()).decode(
            app.state.registered_asa[P.Bytes("aura")].get()
        ),
        (aura_id := P.abi.Uint64()).set(aura_token.asset_id),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetFreeze,
                P.TxnField.freeze_asset: aura_id.get(),
                P.TxnField.freeze_asset_account: address.get(),
                P.TxnField.freeze_asset_frozen: to.get(),
            }
        ),
    )


@P.Subroutine(P.TealType.none)
def pay_95_percent(
    txn: P.abi.PaymentTransaction, price: P.abi.Uint64, receiver: P.abi.Address
):
    return P.Seq(
        P.Assert(
            txn.get().amount() == price.get(),
            comment="Transaction price is not the required amount",
        ),
        P.Assert(
            txn.get().receiver() == P.Global.current_application_address(),
            comment="Transaction receiver has to be the app Address",
        ),
        (nity_five_percent := P.abi.Uint64()).set(
            P.Div(price.get() * P.Int(5), P.Int(100))
        ),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.Payment,
                P.TxnField.amount: nity_five_percent.get(),
                P.TxnField.sender: P.Global.current_application_address(),
                P.TxnField.receiver: receiver.get(),
            }
        ),
    )
