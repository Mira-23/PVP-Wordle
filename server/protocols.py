class Protocols:
    class Response:
        NICKNAME = "protocol.request_nickname"
        GUESSES = "protocol.guesses"
        START = "protocol.start"
        OPPONENT = "protocol.opponent"
        OPPONENT_ADVANCE = 'protocol.opponent_advance'
        ANSWER_VALID = "protocol.answer_valid"
        INVALID_REQUEST = 'protocol.invalid_request'
        WINNER = "protocol.winner"
        OPPONENT_LEFT = "protocol.opponent_left"
        NEW_ROUND = "protocol.new_round"
        SETTINGS = "protocol.settings"
        POINTS_UPDATE = "protocol.points_update"

    class Request:
        ANSWER = "protocol.answer"
        NICKNAME = "protocol.send_nickname"
        LEAVE = "protocol.leave"
        JOIN_GAME = "protocol.join_game"
        CREATE_GAME = "protocol.create_game"