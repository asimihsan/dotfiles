from scipy.stats import poisson


def run_main():
    # Config file parameters
    users_per_step = 50
    total_steps = 30

    # Derived parameter
    N = users_per_step * total_steps  # Total number of users at the end of ramp-up

    # Given parameter in the scenario
    lambda_per_user = 0.01  # Rate parameter (λ) for each user

    # Calculate the expected mean rate of actions per second for all users combined
    mean_actions_per_second = N * lambda_per_user

    # Calculate the 95th percentile of actions per second
    aggregate_lambda = N * lambda_per_user
    k_95th_percentile = poisson.ppf(0.95, aggregate_lambda)

    print(f"Expected Mean Actions per Second: {mean_actions_per_second}")
    print(f"Expected 95th Percentile of Actions per Second: {k_95th_percentile}")


if __name__ == "__main__":
    run_main()
