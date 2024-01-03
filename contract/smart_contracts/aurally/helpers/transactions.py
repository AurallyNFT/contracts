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
