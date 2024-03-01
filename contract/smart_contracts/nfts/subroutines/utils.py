import pyteal as P


@P.Subroutine(P.TealType.none)
def calculate_and_update_network_difficulty():
    """
    Calculates the network difficulty based on the given parameters.

    Parameters:
    - s: number of transactions in the current epoch
    - st: target number of transactions in the current epoch
    - d_prev: difficulty of the previous epoch
    - dl: minimum difficulty
    - e: difference between s and st

    Calculates:
    - d: difficulty
    """
    from smart_contracts.nfts.contract import app

    e = P.abi.Uint64()
    d = P.abi.Uint64()
    return P.Seq(
        (dl := P.abi.Uint64()).set(app.state.min_difficulty.get()),
        (s := P.abi.Uint64()).set(app.state.epoch_nft_transactions.get()),
        (st := P.abi.Uint64()).set(app.state.epoch_target_transaction.get()),
        (d_prev := P.abi.Uint64()).set(app.state.network_difficulty.get()),
        P.If(
            s.get() > st.get(),
            P.Seq(
                e.set(s.get() - st.get()),
                d.set((P.Int(1) + e.get() / st.get()) * d_prev.get()),  #
            ),
            P.Seq(
                e.set(st.get() - s.get()),
                d.set((P.Int(1) - e.get() / st.get()) * d_prev.get()),
            ),
        ),
        P.If(
            d.get() > dl.get(),
            app.state.network_difficulty.set(d.get()),
            app.state.network_difficulty.set(dl.get()),
        ),
        app.state.epoch_nft_transactions.set(P.Int(0)),
    )


@P.Subroutine(P.TealType.none)
def calculate_and_update_base_reward():
    """
    Calculates the base reward for each NFT transaction

    Parameters:
    - pa: Total number of Aurally Tokens rewardable
    - n: Total target number of nft transactions on the network

    Calculates:
    - r_bar: Base reward for each transaction
    """
    from smart_contracts.nfts.contract import app

    r_bar = P.abi.Uint64()
    return P.Seq(
        (pa := P.abi.Uint64()).set(app.state.rewardable_tokens_supply.get()),
        (n := P.abi.Uint64()).set(app.state.total_target_nft_sales.get()),
        r_bar.set(pa.get() / n.get()),
        app.state.aura_base_reward.set(r_bar.get()),
    )


@P.Subroutine(P.TealType.none)
def calculate_and_update_reward():
    """
    Calculates the real reward per transaction based on the network difficulty

    Parameters:
    - r_bar: Base reward for each transaction
    - d: Network difficulty

    Calculates:
    r: Real reward for each transaction
    """
    from smart_contracts.nfts.contract import app

    return P.Seq(
        calculate_and_update_network_difficulty(),
        calculate_and_update_base_reward(),
        (r_bar := P.abi.Uint64()).set(app.state.aura_base_reward.get()),
        (d := P.abi.Uint64()).set(app.state.network_difficulty.get()),
        (r := P.abi.Uint64()).set(r_bar.get() / d.get()),
        P.If(
            r.get() > P.Int(0),
            app.state.aura_reward.set(r.get()),
            app.state.aura_reward.set(app.state.min_aural_reward.get()),
        ),
    )
