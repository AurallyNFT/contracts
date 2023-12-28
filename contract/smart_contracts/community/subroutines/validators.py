import pyteal as P


@P.Subroutine(P.TealType.none)
def ensure_zero_payment(txn: P.abi.PaymentTransaction):
    return P.Assert(
        txn.get().amount() == P.Int(0), comment="Payment amount should be 0"
    )


@P.Subroutine(P.TealType.none)
def ensure_sender_is_app_creator(txn: P.abi.Transaction):
    return P.Assert(
        txn.get().sender() == P.Global.creator_address(),
        comment="Not app creator: You are not authorised to perform this action",
    )


@P.Subroutine(P.TealType.none)
def ensure_is_admin_or_app_creator(addr: P.abi.Address):
    from smart_contracts.community.contract import app

    return P.Seq(
        P.Assert(
            P.Or(
                addr.get() == P.Global.creator_address(),
                app.state.admins[addr.get()].get() == P.Bytes("True"),
            ),
            comment="Not admin: You are not authorised to perform this action",
        ),
    )
