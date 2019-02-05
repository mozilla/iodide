import React from "react";
import PropTypes from "prop-types";
import styled from "react-emotion";
import DoubleChevronIcon from "../double-chevron-icon";
import BaseIcon from "./base-icon";
import ConsoleContainer from "./console-container";
import ConsoleGutter from "./console-gutter";
import THEME from "../../../../shared/theme";

// we have to offset this icon since it does not
// follow the material design ones
const DoubleChevron = styled(BaseIcon(DoubleChevronIcon))`
  margin: 0;
  opacity: 0.3;
`;

const backgroundColor = (o = 1) => `rgba(251,251,253, ${o})`;

const InputContainer = styled(ConsoleContainer)`
  overflow: auto;
  margin-bottom: 0px;
  margin-top: 0px;
  background-color: ${backgroundColor()};
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
`;

const InputBody = styled("pre")`
  padding:0;
  margin: 0;
  padding-top:5px;
  padding-bottom:5px;
  font-size: ${THEME.client.console.fontSize};
  line-height: ${THEME.client.console.lineHeight};
  font-family: monospace;
  grid-column: 2 / 4;
  opacity:.7;

  :before {
    font-family: sans-serif;
    content: "${props => props.language || ""}";
    border-left: 1px solid rgba(0, 0, 0, 0.2);
    border-bottom: 1px solid rgba(0, 0, 0, 0.2);
    border-bottom-left-radius: 3px;
    color: rgba(0,0,0,.6);
    background-color: ${backgroundColor(0.9)};
    padding-right:7px;
    padding-left:7px;
    padding-top:3px;
    float: right;
    font-size:10px;
    transform: translate(0px, -8px);
  }
`;

InputBody.propTypes = {
  language: PropTypes.string
};

export default class ConsoleInput extends React.Component {
  static propTypes = {
    language: PropTypes.string.isRequired
  };
  render() {
    return (
      <InputContainer>
        <ConsoleGutter side="left">
          <DoubleChevron />
        </ConsoleGutter>
        <InputBody language={this.props.language}>
          {this.props.children.trim()}
        </InputBody>
      </InputContainer>
    );
  }
}
