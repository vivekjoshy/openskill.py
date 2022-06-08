from openskill import Rating, rate, predict_win

x, y = Rating(), Rating()

mu_precision = 1 + 0.0001 / 365
sigma_precision = 1 + 1 / 365

# Let player X win 66% of the games.
for match in range(10000):
    if match % 3:
        [[x], [y]] = rate([[x], [y]])
    else:
        [[y], [x]] = rate([[y], [x]])

    # Decay Rating - Assume 1 Match Per Day
    x.mu /= mu_precision
    y.mu /= mu_precision

    x.sigma *= sigma_precision
    y.sigma *= sigma_precision

print("Before Large Decay: ")
print(f"Player X: mu={x.mu}, sigma={x.sigma}")
print(f"Player Y: mu={y.mu}, sigma={y.sigma}\n")

print("Predict Winner Before Decay:")
x_percent, y_percent = predict_win([[x], [y]])
print(f"X has a {x_percent * 100: 0.2f}% chance of winning over Y\n")

# Decay Rating - Assume 365 Days Passed
for match in range(365):

    # Only player X's rating has decayed.
    if (x.mu < 25 + 3 * 25 / 3) or (x.mu > 25 - 3 * 25 / 3):
        x.mu /= mu_precision

    if x.sigma < 25 / 3:
        x.sigma *= sigma_precision

print("Player X's Rating After Decay: ")
print(f"Player X: mu={x.mu}, sigma={x.sigma}\n")

# One Match b/w X and Y
[[x], [y]] = rate([[x], [y]])
x.mu /= mu_precision
y.mu /= mu_precision
x.sigma *= sigma_precision
y.sigma *= sigma_precision


print("After Large Decay (1 Year): ")
print(f"Player X: mu={x.mu}, sigma={x.sigma}")
print(f"Player Y: mu={y.mu}, sigma={y.sigma}\n")

print("Predict Winner After Decay:")
x_percent, y_percent = predict_win([[x], [y]])
print(f"X has a {x_percent * 100: 0.2f}% chance of winning over Y")
