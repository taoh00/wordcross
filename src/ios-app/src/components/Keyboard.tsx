/**
 * 虚拟键盘组件
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';

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
  const keyWidth = (screenWidth - 32 - 9 * 4) / 10;
  const keyHeight = keyWidth * 1.3;
  
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
                activeOpacity={0.6}
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
    paddingVertical: 12,
    backgroundColor: '#E5E7EB',
    borderTopWidth: 1,
    borderTopColor: '#D1D5DB',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 6,
  },
  key: {
    backgroundColor: '#fff',
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  deleteKey: {
    backgroundColor: '#9CA3AF',
  },
  keyText: {
    fontSize: 18,
    fontWeight: '500',
    color: '#1F2937',
  },
  deleteKeyText: {
    fontSize: 20,
    color: '#fff',
  },
});
