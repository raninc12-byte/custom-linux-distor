import QtQuick 2.0

Presentation {
    id: presentation

    Timer {
        interval: 5000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Image { source: "welcome.png"; anchors.centerIn: parent }
        Text {
            text: "Meet your built-in local AI assistant - runs fully offline, no cloud."
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            font.pointSize: 16
        }
    }

    Slide {
        Text {
            text: "Ask it to explain errors, suggest fixes, or manage installed AI models -\nit never runs a command without your say-so."
            anchors.centerIn: parent
            font.pointSize: 16
            wrapMode: Text.WordWrap
            width: parent.width * 0.8
            horizontalAlignment: Text.AlignHCenter
        }
    }

    Slide {
        Text {
            text: "GPU drivers (integrated, or NVIDIA - open-source or proprietary as needed)\nare auto-detected and configured on first boot - nothing to configure manually."
            anchors.centerIn: parent
            font.pointSize: 16
            wrapMode: Text.WordWrap
            width: parent.width * 0.8
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
