workspace "C4 Model Notation" "Visual reference for C4 Model symbols and colors" {

    model {
        # Example persons
        user = person "User" "A user of the software system"
        admin = person "Administrator" "System administrator"

        # Example systems
        mainSystem = softwareSystem "Software System" "The software system being described" {
            webApp = container "Web Application" "Provides web interface" "React/TypeScript" {
                loginComponent = component "Login Component" "Handles user authentication" "React Component"
                dashboardComponent = component "Dashboard Component" "Shows system overview" "React Component"
            }
            api = container "API Application" "Provides REST API" "Spring Boot/Java"
            database = container "Database" "Stores system data" "PostgreSQL" "Database"
        }
        externalSystem = softwareSystem "External System" "An external system" "External System"

        # Example relationships
        user -> mainSystem "Uses"
        admin -> mainSystem "Administers"
        mainSystem -> externalSystem "Integrates with"

        user -> webApp "Uses" "HTTPS"
        webApp -> api "Makes API calls to" "JSON/HTTPS"
        api -> database "Reads from and writes to" "SQL/TCP"
        api -> externalSystem "Calls" "REST/HTTPS"

        loginComponent -> api "Authenticates via" "REST API"
        dashboardComponent -> api "Gets data from" "REST API"
    }

    views {
        # C4 Notation reference diagram showing all element types
        systemContext mainSystem "C4Notation" {
            include *
            title "C4 Model Notation Reference"
            description "Official C4 Model symbols, colors, and element types"
            autoLayout tb
        }

        # Container view showing container-level elements
        container mainSystem "NotationContainers" {
            include *
            title "C4 Container Level Notation"
            description "Container-level elements with official colors and shapes"
            autoLayout tb
        }

        # Component view showing component-level elements
        component webApp "NotationComponents" {
            include *
            title "C4 Component Level Notation"
            description "Component-level elements with official colors and shapes"
            autoLayout tb
        }

        styles {
            # Official C4 Model colors and styling by Simon Brown
            element "Person" {
                shape Person
                background #08427b
                stroke #052e56
                color #ffffff
                fontSize 22
                metadata false
            }
            element "Software System" {
                background #1168bd
                stroke #0b4884
                color #ffffff
                fontSize 24
                shape RoundedBox
                metadata false
            }
            element "External System" {
                background #999999
                stroke #777777
                color #ffffff
                fontSize 24
                shape RoundedBox
                metadata false
            }
            element "Container" {
                background #438dd5
                stroke #2e7cb8
                color #ffffff
                fontSize 20
                shape RoundedBox
                metadata false
            }
            element "Component" {
                background #85bbf0
                stroke #5a9bd4
                color #000000
                fontSize 18
                shape RoundedBox
                metadata false
            }
            element "Database" {
                shape Cylinder
                background #23a2f0
                stroke #1a7bb8
                color #ffffff
                fontSize 20
            }

            # Relationship styles
            relationship "Relationship" {
                thickness 2
                color #707070
                dashed false
                routing Orthogonal
                fontSize 16
                width 200
                position 50
                opacity 100
            }
        }

        # No branding needed for notation reference
    }
}
