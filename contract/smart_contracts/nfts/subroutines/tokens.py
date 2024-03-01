import pyteal as P
from smart_contracts.nfts.boxes import AurallyToken


@P.Subroutine(P.TealType.none)
def bootstrap_token(
    asset_key: P.abi.String,
    total: P.abi.Uint64,
    unit_name: P.abi.String,
    url: P.abi.String,
):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        P.Assert(
            P.Not(app.state.registered_asa[asset_key.get()].exists()),
            comment="Aura tokens already exist",
        ),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_total: total.get(),
                P.TxnField.config_asset_name: asset_key.get(),
                P.TxnField.config_asset_unit_name: unit_name.get(),
                P.TxnField.config_asset_url: url.get(),
                P.TxnField.config_asset_decimals: P.Int(6),
                P.TxnField.config_asset_metadata_hash: P.Bytes(
                    bytes.fromhex(
                        "b16164a8448b4c255579d1baa714031c8edc47fac09c7d446f066bc25eace020"
                    )
                ),
                P.TxnField.config_asset_freeze: P.Global.current_application_address(),
                P.TxnField.config_asset_manager: P.Global.current_application_address(),
                P.TxnField.config_asset_reserve: P.Global.current_application_address(),
                P.TxnField.config_asset_clawback: P.Global.current_application_address(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (token := AurallyToken()).set(asset_id, asset_key, total),
        app.state.registered_asa[asset_key.get()].set(token),
    )
