#define CATCH_CONFIG_MAIN
#include "catch_amalgamated.hpp"

TEST_CASE("Grouped sanity tests", "[sanity]") {
    SECTION("1?") {
        REQUIRE(1 == 1);
    }
    SECTION("2?") {
        REQUIRE(2 == 2);
    }
    SECTION("3?") {
        REQUIRE(3 == 3);
    }
    SECTION("4?") {
        REQUIRE(4 == 4);
    }
}