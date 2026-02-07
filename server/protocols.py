from typing import ClassVar

class Protocols:
    class Response:
        NICKNAME: ClassVar[str] = "protocol.request_nickname"
        GUESSES: ClassVar[str] = "protocol.guesses"
        START: ClassVar[str] = "protocol.start"
        OPPONENT: ClassVar[str] = "protocol.opponent"
        OPPONENT_ADVANCE: ClassVar[str] = "protocol.opponent_advance"
        ANSWER_VALID: ClassVar[str] = "protocol.answer_valid"
        INVALID_REQUEST: ClassVar[str] = "protocol.invalid_request"
        WINNER: ClassVar[str] = "protocol.winner"
        OPPONENT_LEFT: ClassVar[str] = "protocol.opponent_left"
        NEW_ROUND: ClassVar[str] = "protocol.new_round"
        SETTINGS: ClassVar[str] = "protocol.settings"
        POINTS_UPDATE: ClassVar[str] = "protocol.points_update"
        LEADERBOARD: ClassVar[str] = "protocol.leaderboard"

    class Request:
        ANSWER: ClassVar[str] = "protocol.answer"
        NICKNAME: ClassVar[str] = "protocol.send_nickname"
        LEAVE: ClassVar[str] = "protocol.leave"
        JOIN_GAME: ClassVar[str] = "protocol.join_game"
        CREATE_GAME: ClassVar[str] = "protocol.create_game"
        GET_LEADERBOARD: ClassVar[str] = "protocol.get_leaderboard"
