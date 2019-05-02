import React from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import styled from "react-emotion";

import AppMessage from "./console/app-message";
import ValueRenderer from "../reps/value-renderer";

import HistoryInputItem from "./console/history-input-item";
import ConsoleMessage from "./console/console-message";

import { getHistoryItemById } from "../../../shared/state-selectors/history-selectors";

const PreText = styled("pre")`
  padding: 0;
  margin: 0;
`;

export class HistoryItemUnconnected extends React.Component {
  static propTypes = {
    content: PropTypes.string,
    level: PropTypes.string,
    historyId: PropTypes.string.isRequired,
    historyType: PropTypes.string.isRequired,
    fetchMessage: PropTypes.string,
    language: PropTypes.string
  };
  static whyDidYouRender = true;

  render() {
    switch (this.props.historyType) {
      case "APP_MESSAGE":
        return <AppMessage messageType={this.props.content} />;
      case "CONSOLE_MESSAGE": {
        // CONSOLE_MESSAGEs are non eval input / output messages.
        // examples: implicit plugin load statuses / errors, eventually browser console
        // interception.
        return (
          <ConsoleMessage level={this.props.level}>
            {this.props.content}
          </ConsoleMessage>
        );
      }
      case "CONSOLE_INPUT": {
        // returns an input.
        return (
          <HistoryInputItem language={this.props.language}>
            {this.props.content}
          </HistoryInputItem>
        );
      }
      case "CONSOLE_OUTPUT": {
        return (
          <ConsoleMessage level={this.props.level || "OUTPUT"}>
            <ValueRenderer
              valueContainer="IODIDE_EVALUATION_RESULTS"
              valueKey={this.props.historyId}
            />
          </ConsoleMessage>
        );
      }
      case "FETCH_CELL_INFO": {
        return (
          <ConsoleMessage level={this.props.level || "OUTPUT"}>
            <PreText>{this.props.fetchMessage}</PreText>
          </ConsoleMessage>
        );
      }
      default:
        return (
          <ConsoleMessage level="warn">
            Unknown history type {this.props.historyType}
          </ConsoleMessage>
        );
    }
  }
}

export function mapStateToProps(state, ownProps) {
  return getHistoryItemById(state, ownProps.historyId);
}

export default connect(mapStateToProps)(HistoryItemUnconnected);
