"""Small manual test for the beginner-friendly demand prediction module."""

from prediction import predict_demand, train_model


if __name__ == "__main__":
    train_model()
    prediction = predict_demand("H001", "M001")
    print(f"Example prediction for H001 and M001: {prediction:.2f} units")