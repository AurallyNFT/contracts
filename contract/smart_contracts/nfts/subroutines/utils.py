import pyteal as P


@P.Subroutine(P.TealType.none)
def calculate_and_update_network_difficulty():
    """
    Calculates the network difficulty based on the given parameters.

    Parameters:
    - a (alpha): Scalling contstant (1 <= a < 10)
    - s: Number of actual NFT transactions in the current epoch
    - st: Target number of NFT transactions for the current epoch
    - d_prev: Difficulty of the previous epoch

    Returns:
    - D: Calculated difficulty for the current epoch
    """
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (scaling_constant := P.abi.Uint64()).set(app.state.scaling_constant.get()),
        (nft_transactions := P.abi.Uint64()).set(
            app.state.epoch_nft_transactions.get()
        ),
        (target_no_transactions := P.abi.Uint64()).set(
            app.state.epoch_target_transaction.get()
        ),
        (curr_difficulty := P.abi.Uint64()).set(app.state.network_difficulty.get()),
        (new_difficulty := P.abi.Uint64()).set(
            (
                P.Int(1)
                + (
                    scaling_constant.get()
                    - nft_transactions.get() * target_no_transactions.get()
                )
                / target_no_transactions.get()
            )
            * curr_difficulty.get(),
        ),
        P.If(
            new_difficulty.get() == P.Int(0),
            app.state.network_difficulty.set(P.Int(1)),
            app.state.network_difficulty.set(new_difficulty.get()),
        ),
    )
    # return (P.Int(1) + s.get() - (st.get() * d_prev.get()) / a.get()) / (
    #     P.Int(10) * st.get()
    # )


@P.Subroutine(P.TealType.none)
def calculate_and_update_base_reward():
    """
    Calculates the base reward for each NFT transaction

    Parameters:
    - a: Total supply of aurally tokens
    - p: Percentage of aurally tokens reserved for network participants
    - n: Total number of NFT sales on the network

    Returns:
    - base_reward: Base reward for each transaction
    """
    # return p.get() * a.get() / n.get()
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (total_auras := P.abi.Uint64()).set(app.state.total_aurally_tokens.get()),
        (percentage := P.abi.Uint64()).set(
            (
                app.state.rewardable_tokens_supply.get()
                / app.state.total_aurally_tokens.get()
            )
            * P.Int(100)
        ),
        (nft_sales := P.abi.Uint64()).set(app.state.total_nft_transactions.get()),
        app.state.aura_base_reward.set(
            percentage.get() * (total_auras.get() / (nft_sales.get() * P.Int(10))),
        ),
    )


@P.Subroutine(P.TealType.none)
def calculate_and_update_reward():
    """
    Calculates the real reward per transaction based on the network difficulty

    Parameters:
    - base_reward: Base reward for each transaction
    - difficulty: Network difficulty for the current epoch

    Returns:
    - reward: Adjusted reward per transaction
    """
    from smart_contracts.nfts.contract import app

    return P.Seq(
        calculate_and_update_network_difficulty(),
        # calculate_and_update_base_reward(),
        # (difficulty := P.abi.Uint64()).set(app.state.network_difficulty.get()),
        # (base_reward := P.abi.Uint64()).set(app.state.aura_base_reward.get()),
        # app.state.aura_reward.set(base_reward.get() / difficulty.get()),
    )
