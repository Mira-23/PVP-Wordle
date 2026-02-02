class Protocols:
    class Response:
        NICKNAME = "protocol.request_nickname"
        GUESSES = "protocol.guesses"
        START = "protocol.start"
        OPPONENT = "protocol.opponent"
        OPPONENT_ADVANCE = 'protocol.opponent_advance'
        ANSWER_VALID = "protocol.answer_valid"
        ANSWER_INVALID = 'protocol.answer_invalid'
        WINNER = "protocol.winner"
        OPPONENT_LEFT = "protocol.opponent_left"
        NEW_ROUND = "protocol.new_round"

    class Request:
        ANSWER = "protocol.answer"
        NICKNAME = "protocol.send_nickname"
        LEAVE = "protocol.leave"