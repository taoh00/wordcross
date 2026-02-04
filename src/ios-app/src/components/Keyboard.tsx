/**
 * 虚拟键盘组件 (Kawaii Style)
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions, Platform } from 'react-native';
import { COLORS, SHADOWS, LAYOUT } from '../utils/theme';

interface KeyboardProps {
  onKeyPress: (key: string) => void;
  onDelete: () => void;
}

const { width: screenWidth } = Dimensions.get('window');

const ROWS = [
  ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
  ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
  ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫'],
];

export default function Keyboard({ onKeyPress, onDelete }: KeyboardProps) {
  const handlePress = (key: string) => {
    if (key === '⌫') {
      onDelete();
    } else {
      onKeyPress(key);
    }
  };
  
  // 计算按键大小
  // 留出边距: padding(8) + gap(4 * 9)
  const availableWidth = screenWidth - 16;
  const keyWidth = Math.floor((availableWidth - 36) / 10);
  const keyHeight = keyWidth * 1.35;
  
  return (
    <View style={styles.keyboard}>
      {ROWS.map((row, rowIndex) => (
        <View key={rowIndex} style={styles.row}>
          {row.map((key) => {
            const isDelete = key === '⌫';
            
            return (
              <TouchableOpacity
                key={key}
                style={[
                  styles.key,
                  {
                    width: isDelete ? keyWidth * 1.5 : keyWidth,
                    height: keyHeight,
                  },
                  isDelete && styles.deleteKey,
                ]}
                onPress={() => handlePress(key)}
                activeOpacity={0.5}
              >
                <Text
                  style={[
                    styles.keyText,
                    isDelete && styles.deleteKeyText,
                  ]}
                >
                  {key}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  keyboard: {
    paddingHorizontal: 8,
    paddingTop: 12,
    paddingBottom: Platform.OS === 'ios' ? 34 : 20, // 适配 iPhone 底部
    backgroundColor: COLORS.background, // 与页面背景一致，不单独设色
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 8,
  },
  key: {
    backgroundColor: COLORS.white,
    borderRadius: 12, // 更圆润
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 2,
    // 3D Button effect
    borderBottomWidth: 4,
    borderBottomColor: '#FFB6C1', // gray-200
    borderWidth: 1,
    borderTopColor: '#FDFDFD',
    borderLeftColor: '#FDFDFD',
    borderRightColor: '#FDFDFD',
  },
  deleteKey: {
    backgroundColor: COLORS.pink.light,
    borderBottomColor: COLORS.pink.main,
    borderTopColor: COLORS.pink.light,
    borderLeftColor: COLORS.pink.light,
    borderRightColor: COLORS.pink.light,
  },
  keyText: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textMain,
    fontFamily: Platform.OS === 'ios' ? 'Nunito-Bold' : 'sans-serif-medium',
  },
  deleteKeyText: {
    fontSize: 20,
    color: COLORS.pink.dark,
  },
});
