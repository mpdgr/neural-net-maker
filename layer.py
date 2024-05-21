import random
from activation import *
from dropout import *
from util.matrix_util import *
import logging as log


class Layer:
    class Location(Enum):
        INPUT = auto()
        HIDDEN = auto()
        OUTPUT = auto()

    node_count = None
    input_count = None
    location = None
    weights = None
    activation = None
    dropout_rate = 0
    __prediction = None
    __net_prediction = None
    __delta = None
    __gradient = None
    __gradient_alpha = None
    __loss_backprop = None
    __drop_indices = None
    __inp = None
    __alpha = None

    def __init__(self, node_count, input_count, location, activation, weights="rand", alpha=0.1):
        self.node_count = node_count
        self.input_count = input_count
        self.location = location
        self.activation = activation
        # todo: rand weight optional
        self.weights = weights
        self.__alpha = alpha
        if weights == "const":
            self.init_constant_weights(0.5)
        else:
            self.init_random_weights()

    def forward_pass(self, inp, training=False):
        # for input layer input is forwarded directly eventually after applying dropout
        if self.location == Layer.Location.INPUT and training:
            v, a = apply_dropout(self.dropout_rate, inp)
            self.__prediction = v
            log.debug(f"Forwarding prediction: {self.__prediction}")
            return self.__prediction
        elif self.location == Layer.Location.INPUT:
            self.__prediction = inp
            log.debug(f"Forwarding prediction: {self.__prediction}")
            return self.__prediction

        # for remaining layers:
        # compute raw/net prediction for each node
        raw_prediction = self.__predict(inp)
        self.__net_prediction = raw_prediction

        # apply activation function
        self.__prediction = self.activation(raw_prediction, ActivationType.FUNCTION)

        # apply dropout
        if training:
            drop_prediction, drop_indices = apply_dropout(self.dropout_rate, self.__prediction)
            self.__prediction = drop_prediction
            self.__drop_indices = drop_indices
        # todo: clean updating predictions

        log.debug(f"Forwarding prediction: {self.__prediction}")
        return self.__prediction

    def backward_pass(self, error):
        # apply activation function in backpropagation
        # compute derivative for net input
        net_deriv = self.activation(self.__net_prediction, ActivationType.DERIVATIVE)
        # apply dropout
        net_deriv = apply_backprop_dropout(self.__drop_indices, net_deriv)
        # compute delta
        self.__delta = vector_element_wise_product(error, net_deriv)

        # compute gradient
        self.__gradient = vector_outer_product(self.__inp, self.__delta)

        # compute gradient adjusted with alpha
        self.__gradient_alpha = matrix_scalar_product(self.__gradient, self.__alpha)

        # compute loss to backpropagate
        self.__comp_loss_shares()

        self.__adjust_weights()

        log.debug(f"Backpropagating loss: {self.__loss_backprop}")
        return self.__loss_backprop

    # comp prediction basing on input and weights, apply activation function
    # inp size = node_count
    def __predict(self, inp):
        self.__inp = inp
        self.__prediction = matrix_product(inp, self.weights)
        log.debug(f"Prediction: {self.__prediction}")
        return self.__prediction

    # comp summed weight delta products to back propagate to each of input nodes
    def __comp_loss_shares(self):
        loss_share_matrix = matrix_product(self.weights, transpose_matrix(self.__delta))
        self.__loss_backprop = matrix_to_vector_row_major(loss_share_matrix)
        log.debug(f"Loss shares for input nodes: {self.__loss_backprop}")

    # adjust weights - subtract gradient alpha product from respective weights
    def __adjust_weights(self):
        log.debug(f"Weights before update: {self.weights}")
        self.weights = subtract_matrices(self.weights, self.__gradient_alpha)
        log.debug(f"Weights after update: {self.weights}")

    # node x input
    def init_constant_weights(self, const):
        weights = []
        for r in range(self.input_count):
            row = []
            for n in range(self.node_count):
                row.append(const)
            weights.append(row)

        self.weights = weights
        log.debug(f"Initialized weights: {self.weights}")

    def init_random_weights(self):
        weights = []
        random.seed(12121212)
        for r in range(self.input_count):
            row = []
            for n in range(self.node_count):
                row.append((random.random() - 0.5) * 0.5)
            weights.append(row)

        self.weights = weights
        log.debug(f"Initialized weights: {self.weights}")
